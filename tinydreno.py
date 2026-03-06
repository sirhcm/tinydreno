import ctypes, sys

dll = ctypes.CDLL("./libllvm-qcom.so")

# functions
(create_llvm_instance:=dll.cl_compiler_create_llvm_instance).restype, create_llvm_instance.argtypes = ctypes.c_void_p, []
(compile_source:=dll.cl_compiler_compile_source).restype, compile_source.argtypes = ctypes.c_void_p, [
  ctypes.c_void_p, # llvm instance
  ctypes.c_uint64, # chip id
  ctypes.c_int,    # mode
  ctypes.c_char_p, # options
  ctypes.c_int,    # unknown
  ctypes.c_uint64, # unknown
  ctypes.c_uint64, # unknown
  ctypes.c_char_p, # opencl source
  ctypes.c_uint64, # flags
  ctypes.c_uint64, # unknown
  ctypes.c_void_p, # unknown
]
(link_program:=dll.cl_compiler_link_program).restype, link_program.argtypes = ctypes.c_void_p, [
  ctypes.c_void_p, # llvm instance
  ctypes.c_uint64, # chip id
  ctypes.c_int,    # mode
  ctypes.c_char_p, # options
  ctypes.c_int,    # num handles
  ctypes.c_void_p, # input handles (handle_t**)
]
(get_error_code:=dll.cl_compiler_get_error_code).restype, get_error_code.argtypes = ctypes.c_int, [ctypes.c_void_p]
(get_build_log:=dll.cl_compiler_get_build_log).restype, get_build_log.argtypes = ctypes.c_char_p, [ctypes.c_void_p]
(handle_create_binary:=dll.cl_compiler_handle_create_binary).restype, handle_create_binary.argtypes = None, [
  ctypes.c_void_p,                 # handle
  ctypes.POINTER(ctypes.c_void_p), # output ptr
  ctypes.POINTER(ctypes.c_size_t), # output size
]
(free_handle:=dll.cl_compiler_free_handle).restype, free_handle.argtypes = None, [ctypes.c_void_p]
(free_assembly:=dll.cl_compiler_free_assembly).restype, free_assembly.argtypes = None, [ctypes.c_void_p]
(destroy_llvm_instance:=dll.cl_compiler_destroy_llvm_instance).restype, destroy_llvm_instance.argtypes = None, [ctypes.c_void_p]

def compile_cl(src, chip_id):
  inst = create_llvm_instance()
  try:
    ch = compile_source(inst, chip_id, 1, b"", 0, 0, 0, src, 0xa0, 0, None)
    assert get_error_code(ch) == 0, f"compile failed: {get_build_log(ch)}"
    try:
      handles = (ctypes.c_void_p * 1)(ch)
      lh = link_program(inst, chip_id, 1, None, 1, ctypes.addressof(handles))
      assert lh and get_error_code(lh) == 0, f"link failed: {get_build_log(lh) if lh else 'NULL'}"
      try:
        ptr, sz = ctypes.c_void_p(), ctypes.c_size_t()
        handle_create_binary(lh, ctypes.byref(ptr), ctypes.byref(sz))
        try: return ctypes.string_at(ptr.value, sz.value)
        finally: free_assembly(ptr)
      finally: free_handle(lh)
    finally: free_handle(ch)
  finally: destroy_llvm_instance(inst)

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} INPUT OUTPUT")
    exit(1)
  open(sys.argv[2], "wb").write(compile_cl(open(sys.argv[1], "r").read().encode(), 0x6030001))
