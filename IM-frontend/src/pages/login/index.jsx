import { useState } from "react";
import { apiReqs } from "@/api/index";
import { useNavigate } from "react-router-dom";
import { Button, Input, Modal } from "antd";
import imgLogo from './logo.png';
import './login.styl';

function Login() {

    // 创建路由钩子
    const navigate = useNavigate();

    // 组件中自维护的实时数据
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');

    // 登录
    const login = () => {
        apiReqs.signIn({
            data: {
                userName:userName,
                password:password,
            },
            success: (res) => {
                console.log(res)
                navigate('/message')
            },
            fail: (error) => {
                Modal.error({
                    title: '登录失败',
                    content: error.message,
                  })
            }
        })
    }
        
    return (
        <div className="P-login">
            <div className="login-box"> {/* 小框 */}
                <img src={imgLogo} alt="" className="logo" />
                <div className="ipt-con">
                    <Input placeholder="账号" value={userName} onChange={(e) => { setUserName(e.target.value) }} />
                </div>
                <div className="ipt-con">
                    <Input.Password placeholder="密码" value={password} onChange={(e) => { setPassword(e.target.value) }} />
                </div>
                <div className="ipt-con">
                    <Button type="primary" block={true} onClick={login}>
                        登录
                    </Button>
                </div>
                <div className="reg-bar">
                    <a className="reg" href="/#/register">立即注册</a>
                </div>
            </div>
        </div>
    )
    
}

export default Login;