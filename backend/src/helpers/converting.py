import base64


def convert_file_to_base64(file: bytes, file_type: str) -> str:
    return f'data:{file_type};base64,{base64.b64encode(file).decode("utf-8")}'
