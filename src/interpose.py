#!/usr/bin/python

from os.path import splitext, split
from pycparser import c_generator, c_ast, parse_file
from textwrap import dedent
from sys import argv, exit

class InvalidTemplateException(Exception):
   """ A template file has been determined to be invalid during parsing. """
   def __init__(self, msg):
      self.msg = msg
   def __str__(self):
      return self.__repr__()
   def __repr__(self):
      return 'Invalid template file: {0}'.format(self.msg)

def audit(message):
   """ Currently just a thin wrapper for print(). """
   print(">>> {0}".format(message))

def group_replace(text, replacements):
   """ Replaces every occurrence of each item in replacements in the given text. """
   for match, replace in replacements:
      text = text.replace(match, replace)
   return text

class Interpose(object):
   """ Generate and write out code for interposing API calls. The resulting library code can be
       used to intercept API calls for the specified function signatures if it is loaded before
       the original library. On linux, this is achieved with the following variable:
         LD_PRELOAD=/path/to/lib.so
       On OS X, use the following variables:
         DYLD_FORCE_FLAT_NAMESPACE=1 DYLD_INSERT_LIBRARIES=/path/to/lib.dylib
   """
   def __init__(self, header, lib, templates, api):
      self.header = header
      self.lib = lib
      self.api = api
      self.header_path, self.header_base = split(self.header)
      self.header_base = splitext(self.header_base)[0]
      self.templates = {}
      for t in templates:
         type, name = t.split('=')
         ext = splitext(splitext(name)[0])[1]
         path = 'interpose_{0}_{1}{2}'.format(type, self.header_base, ext)
         self.templates[type] = name, path
   def __extract_label(self, template, label):
      """ Given the template string, "before{{LABEL:contents}}after", and the label, "LABEL", this
          function would return the tuple ("before", "after", "contents").
      """
      tag = '{{' + label
      loc = template.find(tag)
      if loc == -1:
         return template, '', ''
      col = template.find(':', loc + len(tag))
      if col == -1:
         end = template.find('}}')
         if end == -1:
            raise InvalidTemplateException("non-terminating '{0}' label".format(label))
         return template[:loc], '', ''
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
         raise InvalidTemplateException("non-terminating '{0}' label".format(label))
      # Adjust for the terminating }} being two characters wide
      return template[:loc], cut[c_pos + 1:], cut[:c_pos - 1]
   def __replace_conditional(self, text, condition, truth):
      while True:
         pre, post, extract = self.__extract_label(text, 'IF_' + condition)
         if not extract:
            break
         text = '{0}{1}{2}'.format(pre, extract if truth else '', post)
      return text
   def __generate_code(self, template_file):
      """ Fills out the provided template with this API. """
      template = ''
      with open(template_file, 'r') as f:
         template = group_replace(
            f.read(),
            (('{{ORIGINAL_HEADER}}', split(self.header)[1]),
             ('{{USER_DEFINED_FUNCTIONS}}', self.templates['usr'][1]),
             ('{{APPLE_LIB_NAME}}', split(self.lib)[1])))
         # Loop until we've filled all 'FOR_EACH_FUNCTION' templates
         while True:
            template_pre, template_post, label = self.__extract_label(template, 'FOR_EACH_FUNCTION')
            if not label:
               break
            label = label.strip()
            func_group = ''
            for name, return_type, arg_names, arg_types, arg_list in self.api:
               func_src = label
               func_src = self.__replace_conditional(func_src, 'NONVOID', return_type != 'void')
               func_src = self.__replace_conditional(func_src, 'VOID', return_type == 'void')
               func_src = group_replace(
                  func_src,
                  (('{{NAME}}', name),
                   ('{{RETURN_TYPE}}', return_type),
                   ('{{ARGUMENT_NAMES}}', arg_names),
                   ('{{ARGUMENT_TYPES}}', arg_types),
                   ('{{ARGUMENT_LIST}}',  arg_list),
                   ('{{,ARGUMENT_NAMES}}', ', ' + arg_names if arg_names else ''),
                   ('{{,ARGUMENT_TYPES}}', ', ' + arg_types if arg_types else ''),
                   ('{{,ARGUMENT_LIST}}',  ', ' + arg_list  if arg_list  else '')))
               func_group += '\n{0}\n'.format(func_src)
            template = '{0}{1}{2}'.format(template_pre, func_group.strip(), template_post)
      return template
   def write(self):
      """ Write the generated code to their respective files. """
      for key, value in self.templates.iteritems():
         template_in, template_out = value
         path = '{0}/{1}'.format(self.header_path or '.', template_out)
         audit("Writing: {0}".format(path))
         with open(path, 'w') as f:
            f.write(self.__generate_code(template_in))

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
                  nstr = '* {0} {1}'.format(' '.join(modifier.quals), nstr)
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
   ast = parse_file(filename, use_cpp = True)
   visitor.visit(ast)
   return visitor.functions

def main(args):
   try:
      header, lib, templates = args[1], args[2], args[3:]
      interpose = Interpose(header, lib, templates, api = parse_header(header))
      interpose.write()
   except InvalidTemplateException as e:
      audit('[ERROR] {0}'.format(e))
      return 1
   else:
      return 0

if __name__ == "__main__":
   exit(main(argv))
