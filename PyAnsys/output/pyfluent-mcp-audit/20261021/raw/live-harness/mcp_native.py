import grpc
from types import SimpleNamespace
from ansys.api.fluent.v0 import scheme_eval_pb2 as pb, scheme_eval_pb2_grpc as rpc
from ansys.fluent.core._grpc_services.scheme_interpreter_service_v0 import Symbol,_convert_py_value_to_scheme_pointer,_convert_scheme_pointer_to_py_value
from pyansys_fluent.connection import resolve_connection_kwargs
def native():
 k=resolve_connection_kwargs('3',start_transcript=False,tcp_timeout_seconds=4)
 c=grpc.insecure_channel(f"{k['ip']}:{k['port']}")
 stub=rpc.SchemeEvalStub(c)
 def evaluate(expr):
  import json
  raw=stub.StringEval(pb.StringEvalRequest(input=expr),metadata=[('password',k['password'])],timeout=30).output
  if raw=='#t':return True
  if raw=='#f':return False
  try:return json.loads(raw)
  except ValueError:return raw

 return SimpleNamespace(scheme=SimpleNamespace(eval=evaluate)),c
