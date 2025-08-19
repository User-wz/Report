# Report
报告简历开发

### API

```json
描述:用户登录
url:http://127.0.0.1:8000/api/v1/logins/login POST
输入:{"username":"","password":""}
输出:{
  "access_token": "eyJhbGciOiJ",
  "token_type": "bearer",
}
描述:用户退出
url:http://127.0.0.1:8000/api/v1/logins/logout POST
输入:"bearer eyJhbGciOiJ"
输出:{"message": "Successfully logged out"}

描述：用户注册
url:http://127.0.0.1:8000/api/v1/users/ POST
输入:{
  "username": "string必填",
  "nickname": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "avatar": "string",
  "password": "string必填",
  "group_id": "0:招聘，1:猎头" 
}
输出:
{
  "username": "string",
  "nickname": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "avatar": "string",
  "id": 0,
  "created_at": "2025-08-19T13:56:29.944Z",
  "updated_at": "2025-08-19T13:56:29.944Z",
  "last_login": "2025-08-19T13:56:29.944Z"
}

描述：获取用户list
url:http://127.0.0.1:8000/api/v1/users/  GET
输入:无
输出：[
  {
    "username": "string",
    "nickname": "string",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "avatar": "string",
    "id": 0,
    "created_at": "2025-08-19T13:57:05.869Z",
    "updated_at": "2025-08-19T13:57:05.869Z",
    "last_login": "2025-08-19T13:57:05.869Z"
  }
]

描述：根据用户检索
url:http://127.0.0.1:8000/api/v1/users/{user_id} GET
输入:user_id
输出:
{
  "username": "string",
  "nickname": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "avatar": "string",
  "id": 0,
  "created_at": "2025-08-19T13:58:04.677Z",
  "updated_at": "2025-08-19T13:58:04.677Z",
  "last_login": "2025-08-19T13:58:04.677Z"
}
描述：根据用户ID检索
url:http://127.0.0.1:8000/api/v1/users/{user_id} PUT
输入:user_id,{
  "username": "string",
  "nickname": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "avatar": "string",
  "password": "string",
  "group_id": 0
}
输出:
{
  "username": "string",
  "nickname": "string",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "avatar": "string",
  "id": 0,
  "created_at": "2025-08-19T13:59:50.606Z",
  "updated_at": "2025-08-19T13:59:50.606Z",
  "last_login": "2025-08-19T13:59:50.606Z"
}

描述：根据用户ID删除
url:http://127.0.0.1:8000/api/v1/users/{user_id} DELET
输入:user_id
输出:{"detail": "用户删除成功"}
```

