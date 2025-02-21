import { createHashRouter, Navigate } from 'react-router-dom';
import Login from '@/pages/login';
import Friend from '@/pages/friend';
import Register from '@/pages/register';
import Message from '@/pages/message';
// 引入Chat页面框架
import Chat from '@/pages/chat';
import { globalConfig } from '@/globalConfig';

// 路由守卫
export function PrivateRoute(props) {
    // 判断localStorage是否有登录用户信息，如果没有则跳转登录页
    return window.localStorage.getItem(globalConfig.SESSION_LOGIN_INFO) ?  (
        props.children
    ) : (
        <Navigate to="/login" />
    )
}

// 全局路由
export const globalRouters = createHashRouter([
    // 精确匹配"/login"，跳转Login页面
    {
        path: '/login',
        element: <Login />,
    },
    {
        path: '/register', // 添加 Register 页面的路由
        element: <Register />,
    },
    
    {
        // 未匹配“/login”，全部进入到chat路由
        path: '/',
        element: <Chat />,
        // 定义Entry二级路由
        children: [
            
            {
                // 精确匹配“/friend”，跳转Friend页面
                path: '/friend',
                element: <Friend />,
            },
            {
                // 精确匹配“/message”，跳转Message页面
                path: '/message',
                element: <Message />,
            },
            {
                // 如果URL没有"#路由",跳转Friend页面
                path: '/',
                element: <Navigate to="/login"/>,
            },
            {
                // 未匹配，跳转Login页面
                path: '*',
                element: <Navigate to="/login" />,
            },
        ],
    },
]);

