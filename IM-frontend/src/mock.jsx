import Mock from 'mockjs';

const domain = '/api/';

// 模拟登录接口
Mock.mock(`${domain}user/login`, 'post', () => {
    return {
        status: 200,
        message: 'OK',
        data: {
            uid: 10000,
            token: 'yyds2023',
            phoneNumber: '13800138000',
            email: '13800138000@qq.com',
        },
    };
});

Mock.mock(`${domain}user/register`, 'put', () => {
    // 返回注册成功的响应
    return {
        status: 200,
        message: '注册成功',
        data: {
            uid: 10000,
            token: 'yyds2023',
            phoneNumber: '13800138000',
            email: '13800138000@qq.com',
        },
    };
});


export default Mock;
