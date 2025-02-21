import React, { useState } from 'react';
import { Outlet } from "react-router-dom";
import { Layout, Input, Button, List, Avatar, Drawer, Menu } from 'antd';
import './chat.styl';
import { ChatOutlined, FriendOutlined, LogoutOutlined} from '@/components/extrakIcons';
import { logout } from '@/api';
import { PrivateRoute } from '@/router';
import FunctionBar from '../../components/functionBar';

const { Header, Content, Footer, Sider } = Layout;

const Chat = () => {
  
 
  return (
      <PrivateRoute>
        <div className="chat-layout">
          <div className='container'>
            < FunctionBar />
            <Outlet />
          </div>
        </div>
      </PrivateRoute>
  );
};

export default Chat;
