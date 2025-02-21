# IM Demo Backend

> 这是一个基于 Django 框架搭建的聊天应用后端示例项目。

## 快速开始

1. 请确保本地已正确安装 Anaconda/Miniconda。
2. 创建一个新的 conda 环境，并激活它：

    ```bash
    conda create -n im_demo python=3.9
    conda activate im_demo
    ```

3. 安装项目依赖：

    ```bash
    pip install -r requirements.txt
    ```

4. 运行数据库迁移，初始化数据库结构：

    ```bash
    python manage.py migrate
    ```

5. 启动开发服务器：

    ```bash
    python manage.py runserver
    ```

6. 打开 http://127.0.0.1:8000 ，可以看到 Django 的 404 页面。

## 实现思路与技术选择

后端使用 Django 框架实现，为实现即时通讯功能，引入了 Channels 库和 Daphne 作为ASGI服务器，以支持 WebSocket 协议。

* **WebSocket & Channels**: WebSocket 用于实现前后端的双向实时通信。通过 Channels，我们将 Django 项目扩展为一个同时支持 HTTP/WebSocket 协议的ASGI应用。Channels 允许我们管理 WebSocket 连接，并在后端通过 [IMDemoConsumer](IMDemo/consumer.py) 处理 WebSocket 事件，如连接、断开、接收消息等。

## API文档

### `POST /messages/`

- **功能描述**: 创建一条新消息
- **请求参数** (body, json):
  - `conversation_id`: 消息所属会话的ID，整型。
  - `username`: 消息发送者的用户名，字符串类型，仅支持字母数字下划线，最长20字符。
  - `content`: 消息内容，字符串类型。
- **返回格式** (json):
  - 新创建的消息([Message](chat/models.py))对象的详细信息
- **说明**:
  - 如果 `conversation_id` 无效或 `username` 不是会话的成员，则返回错误。

### `GET /messages/`

- **功能描述**: 获取消息列表
- **请求参数** (url 参数):
  - `username`: 指定用户的用户名，用于过滤该用户接收到的消息。
  - `conversation_id`: 指定会话的ID，用于过滤属于该会话的消息。
  - `after`: 以 UNIX 毫秒时间戳格式指定开始获取消息的时间点。默认为 0，表示从头开始。
  - `limit`: 指定返回的最大消息数量。默认为 100。
- **返回格式** (json):
  - `messages`: 获取到的消息列表
  - `has_next`: 指示是否还有更多消息可获取
- **说明**:
  - 必须指定 `username` 或 `conversation_id` 中的至少一个参数。
  - 如果指定的 `username` 或 `conversation_id` 不存在，将返回空消息列表。

### `POST /conversations/`

- **功能描述**: 创建一个新会话
- **请求参数** (body, json):
  - `type`: 会话类型，`private_chat` 或 `group_chat`。
  - `members`: 会话成员的用户名列表，每个用户名为字符串类型，仅支持字母数字下划线，最长20字符。
- **返回格式** (json):
  - 新创建的会话([Conversation](chat/models.py))对象的详细信息
- **说明**:
  - 如果 `members` 中包含无效的用户名，则返回错误。
  - 如果是创建私人聊天(`type` 为 `private_chat`)，成员数量必须为2。如果已存在相应的私人聊天，则返回现有会话。

### `GET /conversations/`

- **功能描述**: 获取会话列表
- **请求参数** (url 参数):
  - `id`: 会话ID的列表，用于指定要获取的会话。
- **返回格式** (json):
  - `conversations`: 获取到的会话列表
- **说明**:
  - 如果指定的 `id` 不存在，将不会返回该会话。

### `POST /conversations/{conversation_id}/join`

- **功能描述**: 用户加入一个对话
- **请求参数** (body, json):
  - `username`: 想要加入对话的用户的用户名，字符串类型，仅支持字母数字下划线，最长20字符。
- **返回格式** (json):
  - `result`: 操作结果，成功时为 'success'
- **说明**:
  - 如果 `conversation_id` 无效，则返回404状态码和错误信息。
  - 如果对话类型为 `private_chat`，则不允许加入，并返回403状态码和错误信息。
  - 如果 `username` 无效，则返回404状态码和错误信息。

### `POST /conversations/{conversation_id}/leave`

- **功能描述**: 用户离开一个对话
- **请求参数** (body, json):
  - `username`: 想要离开对话的用户的用户名，字符串类型，仅支持字母数字下划线，最长20字符。
- **返回格式** (json):
  - `result`: 操作结果，成功时为 'success'
- **说明**:
  - 如果 `conversation_id` 无效，则返回404状态码和错误信息。
  - 如果对话类型为 `private_chat`，则不允许离开，并返回403状态码和错误信息。
  - 如果 `username` 无效，则返回404状态码和错误信息。
