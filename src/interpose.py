#!/usr/bin/python

import pycparser
import subprocess
import sys
import os

from pycparser import c_generator, c_ast
from textwrap import dedent

def audit(message):
   """ Currently just a thin wrapper for print(). """
   print(">>> {0}".format(message))

class Interpose(object):
   """ Generate and write out C code for interposing API calls. The resulting library code can be
       used to intercept API calls for the specified function signatures if it is loaded before
       the original library. On linux, this is achieved with the following variable:
         LD_PRELOAD=/path/to/lib.so
       On OS X, use the following variables:
         DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=/path/to/lib.dylib
   """
   def __init__(self, header, lib_template, usr_template, lib, api):
      self.lib_template = lib_template
      self.usr_template = usr_template
      self.real_header = header
      self.real_lib = lib
      self.api = api
      header_path, header_base = os.path.split(header)
      header_base = os.path.splitext(header_base)[0]
      template_ext = os.path.splitext(os.path.splitext(lib_template)[0])[1]
      self.generated_lib_path = '{0}/interpose_lib_{1}{2}'.format(header_path or '.', header_base, template_ext)
      self.generated_usr_path = '{0}/interpose_usr_{1}{2}'.format(header_path or '.', header_base, template_ext)
      self.generated_lib_code = ''
      self.generated_usr_code = ''
      self.wrote = False
   def extract_label(self, template, label):
      tag = '{{' + label
      loc = template.find(tag)
      if loc == -1:
         return template, '', ''
      col = template.find(':', loc + len(tag))
      if col == -1:
         return template, '', ''
      cut = template[col + 1:]
      stack = 2
      c_pos = 0
      found = False
      for c in cut:
         if c == '{':
            stack += 1
         elif c == '}':
            stack -= 1
            if stack == 0:
               found = True
               break
         c_pos += 1
      if not found:
         audit("ERROR: Non-terminating '{0}' tag".format(label))
         sys.exit(1)
      # Adjust for the terminating }} being two-characters wide
      return template[:loc], cut[c_pos + 1:], cut[:c_pos - 1]
   def generate_code(self, template_file):
      template = ''
      with open(template_file, 'r') as f:
         template = f.read()
         template = template.replace('{{ORIGINAL_HEADER}}', os.path.split(self.real_header)[1])
         template = template.replace('{{USER_DEFINED_FUNCTIONS}}', os.path.split(self.generated_usr_path)[1])
         template = template.replace('{{APPLE_LIB_NAME}}', os.path.split(self.real_lib)[1])
         while True:
            template_pre, template_post, label = self.extract_label(template, 'FOR_EACH_FUNCTION')
            if not label:
               break
            label = label.strip()
            func_group = ''
            for func in self.api:
               func_src = label
               func_src = func_src.replace('{{NAME}}', func[0])
               func_src = func_src.replace('{{RETURN_TYPE}}', func[1])
               func_src = func_src.replace('{{ARGUMENT_NAMES}}', func[2])
               func_src = func_src.replace('{{ARGUMENT_TYPES}}', func[3])
               func_src = func_src.replace('{{ARGUMENT_LIST}}', func[4])
               func_src = func_src.replace('{{,ARGUMENT_NAMES}}', ', ' + func[2] if func[2] else '')
               func_src = func_src.replace('{{,ARGUMENT_TYPES}}', ', ' + func[3] if func[3] else '')
               func_src = func_src.replace('{{,ARGUMENT_LIST}}', ', ' + func[4] if func[4] else '')
               while True:
                  func_src_pre, func_src_post, nonvoid = self.extract_label(func_src, 'IF_NONVOID')
                  if not nonvoid:
                     break
                  func_src = '{0}{1}{2}'.format(func_src_pre, nonvoid if func[1] != 'void' else '', func_src_post)
               while True:
                  func_src_pre, func_src_post, void = self.extract_label(func_src, 'IF_VOID')
                  if not void:
                     break
                  func_src = '{0}{1}{2}'.format(func_src_pre, void if func[1] == 'void' else '', func_src_post)
               func_group += '\n{0}\n'.format(func_src)
            template = '{0}{1}{2}'.format(template_pre, func_group.strip(), template_post)
      return template
   def generate_lib_code(self):
      if not self.generated_lib_code:
         self.generated_lib_code = self.generate_code(self.lib_template)
      return self.generated_lib_code
   def generate_usr_code(self):
      if not self.generated_usr_code:
         self.generated_usr_code = self.generate_code(self.usr_template)
      return self.generated_usr_code
   def write(self):
      if self.wrote:
         return
      audit("Writing: {0}".format(self.generated_lib_path))
      with open(self.generated_lib_path, 'w') as f:
         f.write(self.generate_lib_code())
      audit("Writing: {0}".format(self.generated_usr_path))
      with open(self.generated_usr_path, 'w') as f:
         f.write(self.generate_usr_code())
      self.wrote = True

class ParamListVisitor(c_generator.CGenerator):
   def _generate_type(self, n, modifiers=[]):
      """ Recursive generation from a type node. n is the type node. 'modifiers' collects the
          PtrDecl, ArrayDecl and FuncDecl modifiers encountered on the way down to a TypeDecl, to
          allow proper generation from it.

          Note: This is a lightly modified version of the parent method to NOT build in the names.
      """
      typ = type(n)
      
      if typ == c_ast.TypeDecl:
         s = ''
         if n.quals: s += ' '.join(n.quals) + ' '
         s += self.visit(n.type)
         
         # This was changed from the commented-out version so that no names are used
         nstr = '' # n.declname if n.declname else ''
         # Resolve modifiers.
         # Wrap in parens to distinguish pointer to array and pointer to
         # function syntax.
         #
         for i, modifier in enumerate(modifiers):
            if isinstance(modifier, c_ast.ArrayDecl):
               if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                  nstr = '(' + nstr + ')'
               nstr += '[' + self.visit(modifier.dim) + ']'
            elif isinstance(modifier, c_ast.FuncDecl):
               if (i != 0 and isinstance(modifiers[i - 1], c_ast.PtrDecl)):
                  nstr = '(' + nstr + ')'
               nstr += '(' + self.visit(modifier.args) + ')'
            elif isinstance(modifier, c_ast.PtrDecl):
               if modifier.quals:
                  nstr = '* %s %s' % (' '.join(modifier.quals), nstr)
               else:
                  nstr = '*' + nstr
         if nstr: s += ' ' + nstr
         return s
      elif typ == c_ast.Decl:
         return self._generate_decl(n.type)
      elif typ == c_ast.Typename:
         return self._generate_type(n.type)
      elif typ == c_ast.IdentifierType:
         return ' '.join(n.names) + ' '
      elif typ in (c_ast.ArrayDecl, c_ast.PtrDecl, c_ast.FuncDecl):
         return self._generate_type(n.type, modifiers + [n])
      else:
         return self.visit(n)

class FuncDeclVisitor(c_ast.NodeVisitor):
   def __init__(self):
      super(FuncDeclVisitor, self).__init__()
      self.functions = []
   def visit_Decl(self, node):
      """ For each encountered function declaration, this function records a tuple of the following values:
            [0] function name
            [1] return type
            [2] comma-delimited argument names
            [3] comma-delimited argument types
            [4] comma-delimited argument names and types
      """
      if type(node.type) == c_ast.FuncDecl:
         # decl.name can be None in the following situation:
         #    int func(void);
         # In this case, the argument list should be empty. For this reason, we store the list of argument
         # names here so that the argument-types and argument-name-and-type lists can be skipped if there
         # are no arguments.
         arg_names = ', '.join((decl.name or '') for _, decl in node.type.args.children()) if node.type.args else ''
         self.functions.append((
            node.name,
            ParamListVisitor()._generate_type(node.type.type),
            arg_names,
            ParamListVisitor().visit(node.type.args) if arg_names else '',
            c_generator.CGenerator().visit(node.type.args) if arg_names else ''))

def parse_header(filename):
   visitor = FuncDeclVisitor()
   ast = pycparser.parse_file(filename, use_cpp = True)
   visitor.visit(ast)
   return visitor.functions

def main():
   header = sys.argv[1]
   lib_template = sys.argv[2]
   usr_template = sys.argv[3]
   lib = sys.argv[4] if len(sys.argv) > 4 else ''
   interpose = Interpose(header, lib_template, usr_template, lib, api = parse_header(header))
   interpose.write()
   audit('NOTE: Edit the generated "{0}" file, then run "make interpose-lib HEADER={1}"'
         ' to build the interposing library'.format(interpose.generated_usr_path, header))

if __name__ == "__main__":
   main()
