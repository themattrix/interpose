
{{FOR_EACH_FUNCTION:
template<typename Function>
auto {{NAME}}(Function original{{,ARGUMENT_LIST}}) -> {{RETURN_TYPE}}
{
   {{IF_NONVOID:return }}original({{ARGUMENT_NAMES}});
}
}}
