Calling create_global_func_for_List
py_node=List(elts=[Constant(value=1, kind=None), ..., Constant(value=3, kind=None)], ctx=Load())
body:
	Assign(targets=[Name(id='l2bba9486b71e', ctx=Store())], value=Call(func=Name(id='List', ctx=Load(...)), args=[], keywords=[]), type_comment=None)
	Call(func=Attribute(value=Name(id='l2bba9486b71e', ctx=Load(...)), attr='append', ctx=Load()), args=[Constant(value=1, kind=None)], keywords=[])
	Call(func=Attribute(value=Name(id='l2bba9486b71e', ctx=Load(...)), attr='append', ctx=Load()), args=[Constant(value=2, kind=None)], keywords=[])
	Call(func=Attribute(value=Name(id='l2bba9486b71e', ctx=Load(...)), attr='append', ctx=Load()), args=[Constant(value=3, kind=None)], keywords=[])
Evaluating py_expr_Call Call(func=Name(id='List', ctx=Load()), args=[], keywords=[])
Traceback (most recent call last):

ParseError: not implemented yet: Call
  | /mnt/d/spy/l.spy:2
  |     m = [1,2,3]
  |         |_____| this is not supported


