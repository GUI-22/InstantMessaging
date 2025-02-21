### API文档

零、注意事项：

（1）前端的请求体（body）推荐为raw json（而非form-data）

（2）JWT在header的Authorization字段中

（3）用户头像后端返回url，需要再次获取

一、用户模块(后端可以整合为一个APP)

#### url /user/login
1、功能：用户登录

2、方法：POST

3、请求体格式：{"userName": "Ashitemaru", "password": "123456"}

4、成功响应：("token": generate_jwt_token(userName),
            "phoneNumber": user.phoneNumber,
            "email": user.email,
            "picture": user.picture.url)

5、错误：

（1）用户不存在或密码错误
- (2, "password or userName wrong", 401)

（2）重复登录
- (5, "can't login twice", 400)


#### url /user/logout
1、方法：POST

2、请求体格式：{“userName”:”aaa”}（必须带JWT令牌）

3、成功：200 OK

4、错误：

（1）JWT令牌和userName不匹配
- (6, "invalid or expired JWT", 401)

（2）时间冲突user.login_time <= user.logout_time
- (5, "please login first", 400)

（3）请求体中用户名不存在
- (5, "please login first", 400)


#### url /user/register
1、功能：注册，创建User项（还要创建UserReadFriendChainTime项）

2、方法：PUT

3、请求体格式：{"userName": "Ashitemaru", "password": "123456", "ensurePassword": "123456", "phoneNumber": "13243218765", "email":"12345678@qq.com", “picture”:file}
（注意：前端传来“用户头像”是base64编码的文件类型）

4、正确：200 OK

5、错误：

（1）两密码不一致 
- (2， “password and ensurePassword are different”, 400)

（2）所有信息不能有非法字符，小于预定长度（手机号必须13位）

- (3, "userName should be no longer than 255", 400)
- (3, "password should be no longer than 255", 400)
- (3, "email should be no longer than 255", 400)
- (3, "length of phone number should be 11", 400)

（3）用户名已存在
- (2, f"userName {userName} already exists", 400)

（4）检查非法字符
- (4, "only alphabets and number are allowed in userName", 400)
- (4, "Only alphabets and numbers are allowed in password", 400)
- (4, "Only numbers, '-' and '+' are allowed in phoneNumber", 400)
- (4, "Only alphabets, numbers, '@' and '.' are allowed in email", 400)

#### url/user/cancel
1、功能：用户注销账号

2、方法：DELETE

3、请求体格式：{“userName”:”aaa”, "password": "123456"}（必须带JWT令牌）

4、成功：200 OK

5、错误：

（1）JWT鉴权失败（可能因为：过期、（已经登出）无效令牌、名字不匹配）
- (6, "invalid or expired JWT", 401)

（2）密码错误
- (2, "password wrong", 401)

（3）请求体中用户名不存在
- (2, "userName wrong", 401)



#### url/friend/apply_friend
1、功能；申请添加好友
2、方法：POST
3、请求体格式：{“applUserName”:”aaa”}（被申请者的name）
4、成功：200 OK
5、

#### url/friend/handle_friend_apply
1、用户处理别人发给自己的好友申请
- 同意：创建Friends表格、创建conversation（以下简称conv）
- 拒绝：（无操作）
2、方法：POST
3、请求体格式：{"userId":"123", "senderUserId":"456", "agree":"True"/"False"}
- （第一个是自己的userId，第二个是好友申请者的userId）
- "agree":"True"和"False"二选一
4、成功：200 OK
5、

#### url/friend/pull_friend_chain
1、用户拉取好友链
2、方法：GET
3、请求体格式：{“userId”:"123"}（自己的userId）
4、成功：200 OK
5、
（1）JWT鉴权失败（可能因为：过期、（已经登出）无效令牌、名字不匹配）
- (6, "invalid or expired JWT", 401)
返回FriendChain（是根据“最新已读**好友链**时间”进行filter之后的结果）










二、消息模块
#### url/message/{conv_id}
发消息
方法：POST


下拉消息
方法：GET



#### url/message/pull
方法：GET
请求体：
