import React, { useState } from "react";
import { apiReqs } from "@/api/index";
import { useNavigate } from "react-router-dom";
import { Button, Input, Modal } from "antd";
import imgLogo from './logo.png'
import './register.styl';

function Register() {

    const navigate = useNavigate();
    
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [ensurePassword, setEnsurePassword] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [email, setEmail] = useState('');
    const [picture, setPicture] = useState('');


      const handleRegister = () => {
        apiReqs.register({
          data: {
            userName:userName,
            password:password,
            ensurePassword:ensurePassword,
            phoneNumber:phoneNumber,
            email:email,
            picture
          },
          success: (res) => {
            console.log(res);
            navigate('/login');
          },
          fail: (error) => {
            // 处理注册失败情况，例如显示错误信息给用户
            Modal.error({
              title: '注册失败',
              content: error.message,
            })
          },
        });
      }
      

    return (
        <div className="reg-container">
            <img src={imgLogo} alt="" className="logo"/>
            <div className="input-box">
                <Input placeholder="用户名:4-16位大小写英文字母或数字" value={userName} onChange={(e) => setUserName(e.target.value)} />
            </div>
            <div className="input-box">
                <Input.Password placeholder="密码:6-18位大小写英文字母或数字" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="input-box">
                <Input.Password placeholder="确认密码" value={ensurePassword} onChange={(e) => setEnsurePassword(e.target.value)} />
            </div>
            <div className="input-box">
                <Input placeholder="手机号" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} />
            </div>
            <div className="input-box">
                <Input placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="input-box">
                <Button type="primary" onClick={handleRegister}>注册</Button>
            </div>
        </div>
    );
}

export default Register;