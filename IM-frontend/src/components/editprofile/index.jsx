import React, { useState, useEffect } from "react";
import { Modal, Button, Input, message } from "antd";
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { getLocalLoginInfo } from "@/api";
import './editprofile.styl';

function EditProfileModal({ visible, onCancel, onSave }) {
    // 用户信息状态
    const [userInfo, setUserInfo] = useState({
        userName: getLocalLoginInfo().userName,
        phoneNumber: getLocalLoginInfo().phoneNumber,
        email: getLocalLoginInfo().email,
        picture: getLocalLoginInfo().picture,
        newPassword: "", // 新密码字段
        oldPassword: "", // 旧密码字段
    });

    // 是否需要验证密码
    const [needPasswordVerification, setNeedPasswordVerification] = useState(false);

    // 保存用户信息
    const handleSaveProfile = () => {
        if (
            (userInfo.phoneNumber !== getLocalLoginInfo().phoneNumber ||
            userInfo.email !== getLocalLoginInfo().email ||
            userInfo.newPassword) && !needPasswordVerification
        ) {
            setNeedPasswordVerification(true);
            return;
        }

        // 如果需要密码验证，但是输入框为空，则提示用户输入密码
        if (needPasswordVerification && !userInfo.oldPassword) {
            message.info("请输入现有密码以验证身份");
            return;
        }

        // 如果不需要密码验证，或者已经输入了验证密码，则执行保存操作
        onSave(userInfo);
}

    // 取消编辑模式
    const handleCancelEdit = () => {
        onCancel();
    }

    // 处理图片上传
    const handleFileChange = (e) => {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            setUserInfo({ ...userInfo, picture: e.target.result });
        }
        reader.readAsDataURL(file);
    }

    // 监听保存用户信息事件
    useEffect(() => {
        if (needPasswordVerification) {
            if (userInfo.oldPassword) {
                onSave(userInfo);
                setNeedPasswordVerification(false);
            } else {
                message.info("请输入现有密码以验证身份");
            }
        }
    }, [needPasswordVerification]); // 监听 needPasswordVerification 的变化

    return (
        <Modal
            visible={visible}
            onCancel={handleCancelEdit}
            footer={null}
        >
            <div className="edit-profile-modal">
                <div className="input-group">
                    <label htmlFor="userName">用户名</label>
                    <Input
                        id="userName"
                        value={userInfo.userName}
                        onChange={(e) => setUserInfo({ ...userInfo, userName: e.target.value })}
                        placeholder="用户名"
                    />
                </div>
                <div className="input-group">
                    <label htmlFor="phoneNumber">电话</label>
                    <Input
                        id="phoneNumber"
                        value={userInfo.phoneNumber}
                        onChange={(e) => setUserInfo({ ...userInfo, phoneNumber: e.target.value })}
                        placeholder="电话"
                    />
                </div>
                <div className="input-group">
                    <label htmlFor="email">邮箱</label>
                    <Input
                        id="email"
                        value={userInfo.email}
                        onChange={(e) => setUserInfo({ ...userInfo, email: e.target.value })}
                        placeholder="邮箱"
                    />
                </div>
                <div className="input-group">
                    <label htmlFor="newPassword">密码</label>
                    <Input
                        id="newPassword"
                        type="password"
                        value={userInfo.newPassword}
                        onChange={(e) => setUserInfo({ ...userInfo, newPassword: e.target.value })}
                        placeholder="新密码"
                    />
                </div>
                <div className="input-group">
                    <label htmlFor="avatar">头像</label>
                    <input
                        type="file"
                        id="avatar"
                        accept="image/*"
                        onChange={handleFileChange}
                    />
                    {userInfo.picture && <img src={userInfo.picture} alt="Avatar Preview" className="avatar-preview" />}
                </div>
                {needPasswordVerification && (
                    <div className="input-group">
                        <label htmlFor="oldPassword">请输入现有密码以验证身份</label>
                        <Input
                            id="oldPassword"
                            type="password"
                            value={userInfo.oldPassword}
                            onChange={(e) => setUserInfo({ ...userInfo, oldPassword: e.target.value })}
                            placeholder="现有密码"
                        />
                    </div>
                )}
                <div className="button-group">
                    <Button onClick={handleSaveProfile} icon={<SaveOutlined />}>保存</Button>
                    <Button onClick={handleCancelEdit} icon={<CloseOutlined />}>取消</Button>
                </div>
            </div>
        </Modal>
    );
}

export default EditProfileModal;
