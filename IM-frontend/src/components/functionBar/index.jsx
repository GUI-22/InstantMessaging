import React, { useState, useRef, useEffect} from "react";
import { Button, Avatar, Menu, Dropdown, Modal, Input } from "antd";
import { LogoutOutlined, EditOutlined, CloseOutlined } from '@ant-design/icons';
import { ChatOutlined, FriendOutlined } from '@/components/extrakIcons';
import { useNavigate } from "react-router-dom";
import { SESSION_LOGIN_INFO, apiReqs, getLocalLoginInfo } from '@/api';
import EditProfileModal from '@/components/editprofile';
import img from "./1.jpg";
import './functionBar.styl';
import Password from "antd/es/input/Password";

function FunctionBar() {
    const navigate = useNavigate();
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [avatarKey, setAvatarKey] = useState(0); // 添加 key 以重新渲染头像
    const [password, setPassword] = useState('');
    const passwordForCancel = useRef('');
    // 退出登录
    const handleLogout = () => {
        apiReqs.signOut({
            success: (res) => {
                // 清除SESSION_LOGIN_INFO的内容
                window.localStorage.removeItem('SESSION_LOGIN_INFO');
                // 跳转到登录页面
                navigate('/login');
            },      
            fail: (error) => {
                Modal.error({
                    title: '登出失败',
                    content: error.message
                });
            }
        });
    }

    // 编辑用户信息
    const handleEditProfile = () => {
        setEditModalVisible(true);
    }

    // 保存用户信息
    const handleSaveProfile = (userInfo) => {
        apiReqs.modifyUserInfo({
            data: {
                oldPassword: userInfo.oldPassword ,
                newUserName: userInfo.userName === getLocalLoginInfo().userName ? '' : userInfo.userName,
                newPassword: userInfo.newPassword,
                newEmail: userInfo.email === getLocalLoginInfo().email ? '' : userInfo.email,
                newPhoneNumber: userInfo.phoneNumber === getLocalLoginInfo().phoneNumber ? '' : userInfo.phoneNumber,
                newPicture: userInfo.picture === getLocalLoginInfo().picture ? '' : userInfo.picture,
            },
            success: (updatedUserInfo) => {
                window.localStorage.setItem(
                    SESSION_LOGIN_INFO,
                    JSON.stringify({
                        userName: userInfo.userName,
                        phoneNumber: userInfo.phoneNumber,
                        token: getLocalLoginInfo().token,
                        password: userInfo.newPassword || getLocalLoginInfo().password,
                        email: userInfo.email,
                        picture: userInfo.picture 
                    })
                );
                console.log(userInfo.picture);
                setEditModalVisible(false);
                setAvatarKey(prevKey => prevKey + 1); // 更新头像 key，触发重新渲染
                Modal.success({
                    title: '修改成功',
                    content: '您的个人信息已成功修改'
                })
            },
            fail: (error) => {
                Modal.error({
                    title: '修改失败',
                    content: error.message
                })
            }
        });
    }

    // 取消编辑模式
    const handleCancelEdit = () => {
        setEditModalVisible(false);
    }

    // 注销账户
    const handleCancelAccount = () => {
        Modal.confirm({
            title: '确认注销账户',
            content: (
                <div>
                    <p>请输入密码以确认注销账户:</p>
                    <Input.Password
                        onChange={(e) => passwordForCancel.current = e.target.value}
                        placeholder="请输入密码"
                    />
                </div>
            ),
            onOk: () => {
                apiReqs.cancel({
                    data: {
                        password: passwordForCancel.current
                    },
                    success: () => {
                        Modal.success({
                            title: '注销成功',
                            content: '您的账户已成功注销'
                        })
                    },
                    fail: (error) => {
                        console.error("Failed to cancel account:", error);
                        Modal.error({
                            title: '注销失败',
                            content: error.message
                        });
                    }
                });
            },
            onCancel: () => {
                setPassword(''); // 清空密码
            },
        });
    }

    // useEffect(() => {
    //     const handleWindowClose = (event) => {
    //         handleLogout();
    //     };

    //     window.addEventListener('beforeunload', handleWindowClose);

    //     return () => {
    //         window.removeEventListener('beforeunload', handleWindowClose);
    //     };
    // }, []);

    const menu = (
        <Menu>
            <Menu.Item onClick={handleEditProfile} icon={<EditOutlined />}>编辑个人信息</Menu.Item>
            <Menu.Item onClick={handleLogout} icon={<LogoutOutlined />}>退出登录</Menu.Item>
            <Menu.Item onClick={handleCancelAccount} icon={<CloseOutlined />}>注销账户</Menu.Item>
        </Menu>
    );

    return (
        <div className="function-bar">
            <Dropdown overlay={menu} trigger={['click']}>
                <Avatar
                    src={getLocalLoginInfo().picture}
                    alt="User Avatar"
                    className="user-avatar"
                    style={{ cursor: 'pointer' }} // 鼠标悬停样式
                    key={avatarKey} // 添加 key 以重新渲染头像
                />
            </Dropdown>
            <div className="opt-con">
                <Button icon={<ChatOutlined />} onClick={() => { navigate('/message') }} />
                <Button icon={<FriendOutlined />} onClick={() => { navigate('/friend') }} />
            </div>
            <EditProfileModal
                key={editModalVisible} 
                visible={editModalVisible}
                onCancel={handleCancelEdit}
                onSave={handleSaveProfile}
            />
        </div>
    );
}

export default FunctionBar;