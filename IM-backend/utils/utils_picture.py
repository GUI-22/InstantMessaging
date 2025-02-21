import base64
import os
from django.core.files.base import ContentFile

def get_after_second_slash(input_string):
    # 查找第一个"/"的索引
    first_slash_index = input_string.find('/')
    
    # 如果找不到第一个"/"，或者字符串长度小于等于第一个"/"的索引加1（即不存在第二个"/"），则返回原始字符串
    if first_slash_index == -1 or len(input_string) <= first_slash_index + 1:
        return input_string
    
    # 在第一个"/"之后继续查找第二个"/"的索引
    second_slash_index = input_string.find('/', first_slash_index + 1)
    
    # 如果找不到第二个"/"，则返回原始字符串
    if second_slash_index == -1:
        return input_string
    
    # 使用切片返回第二个"/"之后的部分
    return input_string[second_slash_index:]


# 获取用户头像并转换为 base64
def get_base64_image(user):
    if user.picture:
        with open(user.picture.path, "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
            # base64_image = get_after_second_slash[base64_image]
            # filepath = "dataimage/jpegbase64"
            # _, ext = os.path.splitext(user.picture.path)
            # 组合 base64 编码的图像数据和扩展名
            # base64_image = f"data:image/{ext[1:]};base64,{base64_image}"
            new_base64_image = base64_image.replace("dataimage/jpegbase64", "data:image/jpeg;base64,")
            # return "picture!"
            return new_base64_image
    return None
