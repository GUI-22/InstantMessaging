// 暂时用于实现组件外跳转，在home中有引用
import { globalRouters } from '@/router'
import axios from 'axios'
import { Modal } from 'antd'
import { globalConfig  } from '@/globalConfig'

// 配合教程演示组件外路由跳转使用，无实际意义
export const goto = (path) => {
    globalRouters.navigate(path)
}

// 开发环境地址
let API_DOMAIN = '/api/'

if (process.env.NODE_ENV === 'production') {
    // 正式环境地址
    API_DOMAIN = '/api/'
    // 使用nginx反向代理
}


// 用户登录信息在localStorage中存放的名称
export const SESSION_LOGIN_INFO = globalConfig.SESSION_LOGIN_INFO

// API码
export const API_STATUS_CODE = {
    // API请求正常
    OK: 200,
    // API请求正常，数据异常
    ERR_DATA: 403,
    // API请求正常，空数据
    ERR_NO_DATA: 301,
    // API请求正常，登录异常
    ERR_LOGOUT: 401,
}

// API请求异常统一报错提示
export const API_FAILED = '网络请求异常，请稍后再试'
export const API_LOGOUT = '您的账号已在其他设备登录，请重新登录'

export const apiReqs = {
    // user模块：登录（成功后将登录信息存入localStorage）
      signIn: (config) => {
        axios
            .post(API_DOMAIN + 'user/login', config.data)
            .then((res) => {
                let status = res.status;
                let data = res.data;
                config.done && config.done();
                if (status === API_STATUS_CODE.OK) {
                    // 假设生成 JWT 令牌的函数为 generate_jwt_token(userName)
                    window.localStorage.setItem(
                        SESSION_LOGIN_INFO,
                        JSON.stringify({
                            userId: data.userId,
                            userName: config.data.userName,
                            token: data.token,
                            phoneNumber: data.phoneNumber,
                            email: data.email,
                            picture: data.picture 
                        })
                    );
                    config.success && config.success(data);
                } else {
                    config.fail && config.fail(data);
                }
            })
            .catch((error) => {
                config.done && config.done();
                if (error.response) {
                    const status = error.response.status;
                    const data = error.response.data;
                    const info = error.response.data.info;
                    const code = error.response.data.code;
                   
                    config.fail && config.fail({
                        message: info,
                        errorCode: code
                    });
                } else {
                    config.fail && config.fail({
                        message: '网络错误',
                        errorCode: -1
                    })
                }
            });
    },
    
    // user模块：登出（登出后将信息从localStorage删除）
    signOut: (config) => {
        const {userName, token} = getLocalLoginInfo()
        let axiosConfig = {
            method: 'post',
            url: API_DOMAIN + 'user/logout',
            data: {
                userName: userName,
            },
            headers: {
                'Authorization': `${token}` // 在请求头中携带JWT令牌
            }
        }
        axios(axiosConfig)
            .then((res) => {
                let status = res.status;
                let data = res.data;
                if (status === API_STATUS_CODE.OK) {
                    config.success && config.success(data);
                } else {
                    config.fail && config.fail(data);
                }
            })
            .catch((error) => {
                config.done && config.done();
                if (error.response) {
                    const status = error.response.status;
                    const data = error.response.data;
                    const info = error.response.data.info;
                    const code = error.response.data.code;
                   
                    config.fail && config.fail({
                        message: info,
                        errorCode: code
                    });
                } else {
                    config.fail && config.fail({
                        message: "Network error",
                        errorCode: -1
                    });
                }
            });
    },


    // user模块：注册新用户
    register: (config) => {
        axios
            .put(API_DOMAIN + 'user/register', config.data)
            .then((res) => {
                let status = res.status;
                let data = res.data;
                config.done && config.done(data);
                if (status === API_STATUS_CODE.OK) {
                    config.success && config.success(data);
                } else {
                    config.fail && config.fail(data);
                }
            })
            .catch((error) => {
                config.done && config.done();
                if (error.response) {
                    const status = error.response.status;
                    const data = error.response.data;
                    const info = error.response.data.info;
                    const code = error.response.data.code;
                   
                    config.fail && config.fail({
                        message: info,
                        errorCode: code
                    });
                } else {
                    config.fail && config.fail({
                        message: '网络错误',
                        errorCode: -1
                    })
                }
            });
    },
    
    // user模块：注销
    cancel: (config) => {
      const { userName, token } = getLocalLoginInfo();

      let axiosConfig = {
          method: 'delete',
          url: API_DOMAIN + 'user/cancel',
          data: {
              userName: userName,
              password: config.data.password
          },
          headers: {
              'Authorization': token // 在请求头中携带JWT令牌
          }
      };
  
      axios(axiosConfig)
          .then((res) => {
            // 根据返回的状态码执行相应操作
            let status = res.status;
            config.done && config.done(res);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(res);
            } else {
                config.fail && config.fail(res);
            }
          })
          .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
  },

  // user模块：查找用户信息
  pullUserInfo: (config) => {
    const { token } = getLocalLoginInfo(); // 获取JWT令牌

    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'user/pull_user_info?userName=' + config.data.userName,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }

    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(res);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(res.data);
            } else {
                config.fail && config.fail(res);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
  },

// user模块：修改用户信息
  modifyUserInfo: (config) => {
    const { token } = getLocalLoginInfo()
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'user/modify_user_info',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(res);
            } else {
                config.fail && config.fail(res);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: "Network error",
                    errorCode: -1
                });
            }
        });
  },

  // friend模块：添加好友
  applyFriend : (config) => {
    const { token } = getLocalLoginInfo(); // 获取token
    axios.post(API_DOMAIN + 'friend/apply_friend', config.data, {
        headers: {
            'Authorization': token // 替换为您的JWT令牌
        }
    })
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

  // friend模块：拉取新申请好友链
  pullFriendChain : (config) => {
    const { token } = getLocalLoginInfo()
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'friend/pull_friend_chain',
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: "Network error",
                    errorCode: -1
                });
            }
        });
  },

  //friend模块：删除好友
  deleteFriend : (config) => {
    const { token } = getLocalLoginInfo()
    let axiosConfig = {
        method: 'delete',
        url: API_DOMAIN + 'friend/delete_friend',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: "Network error",
                    errorCode: -1
                });
            }
        });
  },

  // friend模块：对好友分组
  groupFriend : (config) => {
      const { token } = getLocalLoginInfo();
      let axiosConfig = {
          method: 'post',
          url: API_DOMAIN + 'friend/grouping_friend',
          data: config.data,
          headers: {
              "Authorization": token // 在请求头中携带JWT令牌
          }
      }
      axios(axiosConfig)
          .then((res) => {
              let status = res.status;
              let data = res.data;
              if (status === API_STATUS_CODE.OK) {
                  config.success && config.success(data);
              }
              else {
                  config.fail && config.fail(data);
              }
              config.done && config.done(); 
          })
          .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: "Network error",
                    errorCode: -1
                });
            }
        });
    },

  // friend模块：处理用户申请
  handleFriendApply : (config) => {
    const { token } = getLocalLoginInfo(); // 获取存储在本地的JWT令牌
    axios.post(API_DOMAIN + 'friend/handle_friend_apply',config.data, {
        headers: {
            'Authorization': token // 替换为您的JWT令牌
        }
    }
    )
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
  },

  // friend模块：拉取好友列表
  pullFriendList : (config) => {
    const { token } = getLocalLoginInfo();
      let axiosConfig = {
          method: 'get',
          url: API_DOMAIN + 'friend/pull_friend_list',
          data: config.data,
          headers: {
              "Authorization": token // 在请求头中携带JWT令牌
          }
      }
      axios(axiosConfig)
          .then((res) => {
              let status = res.status;
              let data = res.data;
              if (status === API_STATUS_CODE.OK) {
                  config.success && config.success(data["total_friend_list"]);
              }
              else {
                  config.fail && config.fail(data);
              }
              config.done && config.done(); 
          })
          .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: "Network error",
                    errorCode: -1
                });
            }
        });
  },

  // message模块：发消息
  sendMessage : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'put',
        url: API_DOMAIN + 'message/send_message',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// message模块：拉取新消息
pullUserChain : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'message/pull_user_chain',
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data["user_chat_chain"]);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// message模块：读取某条消息被回复数
pullReplyCount : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'message/pull_reply_count?messageId=' + config.data.messageId,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// message模块：某条消息阅读的成员列表
pullReaderList : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'message/pull_reader_list?messageId=' + config.data.messageId,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data["reader_list"]);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// message模块：标记在某个会话的read_index
markReadIndex : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'message/mark_read_index',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// message模块：删除消息
deleteMessage : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'delete',
        url: API_DOMAIN + 'message/delete_message',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},



// conversation模块：邀请好友，创建群聊
createConversation : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'put',
        url: API_DOMAIN + 'conversation/create_conversation',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：拉取群聊列表
pullConversationList : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'conversation/pull_conversation_list',
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：拉取会话链
pullConversationChain : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'conversation/pull_conversation_chain?conversationId=' + config.data.conversationId,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：拉取会话的聊天记录
pullConversationChainHistory : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'conversation/pull_conversation_chain_history?conversationId=' + config.data.conversationId +
            "&&earliestTime=" + config.data.earliestTime + "&&memberName=" + config.data.memberName,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：获取群聊成员信息
pullConversationMemberList : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'conversation/pull_conversation_member_list?conversationId=' + config.data.conversationId,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块: 群主指定管理员
appointAdmin : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'conversation/appoint_admin',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：转让群主身份
transferOwnership : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'conversation/transfer_ownership',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：退出群聊
quitConversation : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'delete',
        url: API_DOMAIN + 'conversation/quit_conversation',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：踢出群成员
removeMember : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'delete',
        url: API_DOMAIN + 'conversation/remove_member',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：邀请好友加群
inviteNewMember : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'conversation/invite_new_member',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：获取所有群（自己作为管理员或者群主的群）的入群申请
pullConversationApplyChain : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'get',
        url: API_DOMAIN + 'conversation/pull_conversation_apply_chain?conversationId=' + config.data.conversationId,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

// conversation模块：处理入群申请
handleConversationApply : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'post',
        url: API_DOMAIN + 'conversation/handle_conversation_apply',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},

putAnnouncement : (config) => {
    const { token } = getLocalLoginInfo();
    let axiosConfig = {
        method: 'put',
        url: API_DOMAIN + 'conversation/put_announcement',
        data: config.data,
        headers: {
            "Authorization": token // 在请求头中携带JWT令牌
        }
    }
    axios(axiosConfig)
        .then((res) => {
            let status = res.status;
            let data = res.data;
            config.done && config.done(data);
            if (status === API_STATUS_CODE.OK) {
                config.success && config.success(data);
            } else {
                config.fail && config.fail(data);
            }
        })
        .catch((error) => {
            config.done && config.done();
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                const info = error.response.data.info;
                const code = error.response.data.code;
               
                config.fail && config.fail({
                    message: info,
                    errorCode: code
                });
            } else {
                config.fail && config.fail({
                    message: '网络错误',
                    errorCode: -1
                })
            }
        });
},


}


// 从localStorage获取用户信息
export function getLocalLoginInfo() {
    return JSON.parse(window.localStorage[SESSION_LOGIN_INFO])
}

// 退出登录
export function logout() {
  // 清除localStorage中的登录信息
  window.localStorage.removeItem(SESSION_LOGIN_INFO)
  // 跳转至Login页面
  goto('/login')
}



