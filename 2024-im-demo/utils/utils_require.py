from functools import wraps
import base64

from utils.utils_request import request_failed

MAX_CHAR_LENGTH = 255
PHONE_NUMBER_LENGTH = 11

# A decorator function for processing `require` in view function.
def CheckRequire(check_fn):
    @wraps(check_fn)
    def decorated(*args, **kwargs):
        try:
            return check_fn(*args, **kwargs)
        except Exception as e:
            # Handle exception e
            error_code = -2 if len(e.args) < 2 else e.args[1]
            return request_failed(error_code, e.args[0], 400)  # Refer to below
    return decorated


# Here err_code == -2 denotes "Error in request body"
# And err_code == -1 denotes "Error in request URL parsing"
def require(body, key, type="string", err_msg=None, err_code=-2):
    
    if key not in body.keys():
        raise KeyError(err_msg if err_msg is not None 
                       else f"Invalid parameters. Expected `{key}`, but not found.", err_code)
    
    val = body[key]
    
    err_msg = f"Invalid parameters. Expected `{key}` to be `{type}` type."\
                if err_msg is None else err_msg
    
    if type == "int":
        try:
            val = int(val)
            return val
        except:
            raise KeyError(err_msg, err_code)
    
    elif type == "float":
        try:
            val = float(val)
            return val
        except:
            raise KeyError(err_msg, err_code)
    
    elif type == "string":
        try:
            val = str(val)
            return val
        except:
            raise KeyError(err_msg, err_code)
    
    elif type == "list":
        try:
            assert isinstance(val, list)
            return val
        except:
            raise KeyError(err_msg, err_code)
        
    elif type == "file":
        try:
            val = base64.b64decode(val)  # 将 base64 编码的图片数据解码为二进制数据
            return val
        except:
            raise KeyError(err_msg, err_code)

    else:
        raise NotImplementedError(f"Type `{type}` not implemented.", err_code)
    

def check_illegal_char(check_str, allow_alphabet, allow_number, other_char_list):
    allowed_list = []

    if allow_alphabet:
        allowed_list.extend(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))

    if allow_number:
        allowed_list.extend(list('0123456789'))

    allowed_list.extend(other_char_list)

    for char in check_str:
        if char not in allowed_list:
            return False

    return True
