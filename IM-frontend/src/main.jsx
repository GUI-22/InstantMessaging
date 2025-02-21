import React from "react";
import ReactDOM  from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { globalRouters } from "@/router";
// import App from "./App";
// import App from '@/pages/login'
// import App from '@/pages/home'
// import App from '@/pages/account'
import { ConfigProvider } from "antd";
import { store } from "@/store";
import { Provider } from "react-redux";

// 引入Ant Design中文语言包
import zhCN from "antd/es/locale/zh_CN";
// 全局样式
import "@/common/styles/frame.styl";
/*
if (process.env.NODE_ENV !== 'production') {
    import ('./mock');
}
*/
// 创建一个根React组件，并将指定的DOM节点作为根节点。
// 这个方法会自动处理React组件的初始化、渲染和生命周期管理等功能。
ReactDOM.createRoot(document.getElementById("root")).render(
    <Provider store={store}>
        <ConfigProvider locale={zhCN}>
            <RouterProvider router={globalRouters} />
        </ConfigProvider>
    </Provider>
);
