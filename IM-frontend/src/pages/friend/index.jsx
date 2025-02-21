import React, { useState, useEffect, useRef } from 'react';
import { Button, Input, Modal, Card, List, Avatar } from 'antd';
import { apiReqs } from '@/api'; // 假设导入了申请好友的 API 函数
import { UserAddOutlined } from '@/components/extrakIcons';
import SearchResultModal from '@/components/searchResultModal'; // 引入搜索结果模态框组件
import { SESSION_LOGIN_INFO } from '@/api';
import './friend.styl';
import  rcImg from '@/pages/friend/new-friend.jpg'

const Friend = () => {
    const [applyUserName, setApplyUserName] = useState('');
    const [isSearching, setIsSearching] = useState(false); // 状态用于标识是否正在搜索
    const [searchResult, setSearchResult] = useState([]); // 保存搜索结果
    const [friendList, setFriendList] = useState([]); // 好友列表
    const [searchModalVisible, setSearchModalVisible] = useState(false); // 搜索结果模态框的可见性状态
    const [selectedFriend, setSelectedFriend] = useState(null); // 保存当前选中的好友信息
    const [newFriendRequest, setNewFriendRequest] = useState([]); // 新的好友请求
    const [newGroupName, setNewGroupName] = useState('');
    const [groupMoadalVisible, setGroupMoadalVisible] = useState(false); //设置分组模态框可见性
    const [selectedComponent, setSelectedComponent] = useState("");
    const inputValueRef = useRef('');

    // 展示好友信息的卡片
    function FriendCard({ selectedFriend, handleSendMessage, handleSetGroup, handleDeleteFriend }) {
        return (
            <Card
                title={selectedFriend.friend_name}
                style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}
            >
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <img
                        src={selectedFriend.friend_picture}
                        alt={selectedFriend.friend_name}
                        style={{ width: '100px', height: '100px', borderRadius: '50%' }}
                    />
                </div>
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    <p>用户名: {selectedFriend.friend_name}</p>
                    <p>分组: {selectedFriend.group_name}</p>
                    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '20px' }}>=*/
                        <Button type="primary" style={{ marginRight: '10px' }} onClick={() => handleSetGroup(selectedFriend)}>
                            设置分组
                        </Button>
                        <Button type="primary" danger onClick={() => handleDeleteFriend(selectedFriend)}>
                            删除好友
                        </Button>
                    </div>
                </div>
            </Card>
        );
    }

    function DisplayBox() {
        // 状态：用于保存展示的组件
        const [displayedComponent, setDisplayedComponent] = useState(null);
    
        // 当 selectedComponent 改变时更新展示的组件
        useEffect(() => {
            const renderComponent = () => {
                switch (selectedComponent) {
                    case "friendRequestList":
                        return renderRequestList();
                    case "friendCard":
                        return renderFriendCard();
                    default:
                        return null;
                }
            };
    
            const componentToRender = renderComponent();
            setDisplayedComponent(componentToRender);
        }, [selectedComponent]);
    
        // 好友申请列表展示
        const renderRequestList = () => {
            if (newFriendRequest.length > 0) {
              return (
                <div>
                  {newFriendRequest.length > 0 && (
                    <Card title="新的好友申请" style={{ width: '100%' }}>
                      {newFriendRequest.map(request => (
                        <div key={request.sender_user_id} style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
                            <span style={{ marginRight: '10px' }}>{request.sender_name}</span>
                            <Button type="primary" onClick={() => handleFriendRequest(request,"True")} style={{marginRight:'20px'}}>同意</Button>
                            <Button type="primary" danger onClick={() => handleFriendRequest(request,"False") }>拒绝</Button>
                        </div>
                      ))}
                    </Card>
                  )}
                </div>
              );
            } else {
                
                return null;
            }
        };
    
        // 好友信息卡片展示
        const renderFriendCard = () => {
            if (selectedFriend) {
                return (
                    <FriendCard
                        selectedFriend={selectedFriend}
                        handleSendMessage={sendMessage} // 待补充
                        handleSetGroup={groupFriend}
                        handleDeleteFriend={deleteFriend}
                    />
                );
            } else {
                return null;
            }
        };
    
        // 返回展示的组件
        return displayedComponent;
    }

    // 处理好友申请、删除好友和进行分组后取消选中好友和关闭搜索模态框的逻辑函数
    const handleActionComplete = () => {
        setSelectedFriend(null); // 取消选中好友
        setSearchModalVisible(false); // 关闭搜索模态框
    };

    // 取消搜索状态
    const cancelSearch = () => {
        setIsSearching(false);
        setApplyUserName(''); // 清空搜索框
    };

    // 点击事件：删除好友
    const deleteFriend = (friend) => {
        apiReqs.deleteFriend({
            data: {
                friendUserId: friend.friend_id,
            },
            success: (res) => {
                Modal.success({
                    title: '删除好友成功',
                    content: `已成功删除用户 ${friend.friend_name}`
                });
                // 成功删除后更新页面
                getFriendList(); 
                handleActionComplete(); // 取消选中好友和关闭搜索模态框
            },
            fail: (error) => {
                Modal.error({
                    title: '删除好友失败',
                    content: error.message
                });
            }
        });
    };

    // 点击事件：好友分组
    const groupFriend = (friend) => {
        // 显示输入框让用户输入分组名称
        Modal.confirm({
            title: '输入分组名称',
            content: (
                <Input
                    defaultValue={friend.group_name}
                    placeholder="请输入分组名称"
                    onChange={(e) => inputValueRef.current =  e.target.value}
                />
            ),
            onOk: () => {
                // 调用 API 进行好友分组
                apiReqs.groupFriend({
                    data: {
                        friendIds: [friend.friend_id],
                        groupName: inputValueRef.current // 使用输入框的值
                    },
                    success: (res) => {
                        Modal.success({
                            title: '分组成功',
                            content: `已成功将用户 ${friend.friend_name} 分组到 ${inputValueRef.current}`
                        });
                        getFriendList(); // 在分组好友成功后重新获取好友列表
                        handleActionComplete(); // 取消选中好友和关闭搜索模态框
                    },
                    fail: (error) => {
                        Modal.error({
                            title: '分组失败',
                            content: error.message
                        });
                    }
                });
            },
            onCancel: () => {
                // 用户取消了输入分组名称，不执行任何操作
            },
        });
    };
    

    // 点击事件：搜索用户
    const handleSearchUser = () => {
        apiReqs.pullUserInfo({
            data: {
                userName: applyUserName,
            },
            success: (res) => {
                setSearchResult(res["user_list"]);
                setSearchModalVisible(true);
                
            },
            fail: (error) => {
                Modal.error({
                    title: '搜索用户失败',
                    content: error.message
                });
            }
        })
    };

    // 点击事件：申请添加好友
    const ApplyFriend = (user) => {
        apiReqs.applyFriend({
            data: {
                applyUserName: user.user_name,
            },
            success: (res) => {
                Modal.success({
                    title: '申请添加好友成功',
                    content: '已成功发送好友申请'
                });
            },
            fail: (error) => {
                Modal.error({
                    title: '申请添加好友失败',
                    content: error.message
                });
            }
        })
    };

    // 获取好友列表
    const getFriendList = () => {
        apiReqs.pullFriendList({
            success: (res) => {
                setFriendList(res);
                console.log(friendList);
            },
            fail: (error) => {
                Modal.error({
                    title: '拉取好友列表失败',
                    content: error.message
                });
            }
        });
    };
    

    // 点击事件：拉取申请好友列表
    const pullNewFriendRequest = () => {
        apiReqs.pullFriendChain({
            success: (res) => {
                setNewFriendRequest(res["friend_chain"]);
            },
            fail: (error) => {
                Modal.error({
                    title: '拉取好友申请失败',
                    content: error.message
                })
            }
        });
        setSelectedComponent("friendRequestList");
    };


    // 点击事件：处理好友申请
    const handleFriendRequest = (request, agree) => {
        apiReqs.handleFriendApply(
            {
                data: {
                    senderUserId: request.sender_user_id,
                    agree: agree
                },
                success: (res) => {
                    if (agree === "True") {
                        Modal.success({
                            title: '成功同意',
                            content: `成功添加 ${request.sender_name} `
                        });
                    } else {
                        Modal.success({
                            title: '成功拒绝',
                            content: `成功拒绝 ${request.sender_name} `
                        });
                    }
                    pullNewFriendRequest(); // 重新拉取申请好友列表
                    getFriendList();
                    handleActionComplete(); // 取消选中好友和关闭搜索模态框
                },
                fail: (error) => {
                    Modal.error({
                        title: '处理好友申请失败',
                        content: error.message
                    });
                }
            }
        )
    }

    // 点击事件：展示用户信息
    const handleFriendClick = (friend) => {
        setSelectedFriend(friend); 
        setSelectedComponent("friendCard");
    };

    // 点击事件：切换搜索状态
    const toggleSearchMode = () => {
        setIsSearching(!isSearching);
        setApplyUserName(''); // 清空搜索框
        if (!isSearching) {
            // getFriendList(); // 获取好友列表
        }
    };

    // 点击事件：发消息
    const sendMessage = () => {

    }

    // 渲染搜索框
    const renderSearchBox = () => (
        <div className="search-box">
            <Input
                placeholder="请输入用户名"
                value={applyUserName}
                onChange={(e) => setApplyUserName(e.target.value)}
            />
        </div>
    );

    // 首次渲染完成后执行 getFriendList 
    useEffect(() => {
        getFriendList();
    }, []);

    // 监听页面点击事件，用于取消搜索状态
    useEffect(() => {
        const handleClickOutside = (event) => {
            const container = document.querySelector('.friend-container');
            if (container && !container.contains(event.target)) {
                cancelSearch();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    return (
        <div className="friend-container">
            {/* 用户列表 */}
            <div className="user-list">
                <header className="list-header">
                    {isSearching ? renderSearchBox() : (
                        <>
                            <div className="search-box">
                                <Input
                                    placeholder="搜索"
                                    value={applyUserName}
                                    onChange={(e) => setApplyUserName(e.target.value)}
                                />
                            </div>
                            <div className="add-friend-icon">
                                <Button
                                    type="text"
                                    icon={<UserAddOutlined />}
                                    onClick={toggleSearchMode}
                                />
                            </div>
                        </>
                    )}
                </header>
                {/* 好友列表 */}
                {isSearching ? 
                    <div className='list'>
                        <Button type="primary" block onClick={handleSearchUser}>确认搜索</Button>
                    </div> : (
                    <div className='list'>
                        <p style={{ color:'gray', fontSize: '13px', padding :'5px'}}>新的朋友</p>
                        <Button type="primary" block onClick={pullNewFriendRequest} style={{ display: 'flex', backgroundColor: '#fff', alignItems:'center',borderRadius: '0px', height:'40px'}}>
                            <img src={rcImg} alt='新的朋友'  width="30px" style={{ marginLeft: '5px', marginRight:'50px', verticalAlign: 'middle', borderRadius: '100%'}}></img>
                            <span style={{ color: 'black', fontSize: '14px'}}>新的朋友</span>
                        </Button>
                        <div className="list-item">
                        <List
                            itemLayout="vertical"
                            dataSource={friendList}
                            renderItem={(group) => (
                                <List.Item key={group.group_name}>
                                    <List.Item.Meta
                                        title={<p>{group.group_name}</p>}
                                    />
                                    <div className="list-item">
                                        {group.friend_list.map(friend => (
                                            <div key={friend.friend_id} onClick={() => handleFriendClick(friend)} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                                                <Avatar src={friend.friend_picture} alt={friend.friend_name} size={40} style={{ marginRight: '10px' }} />
                                                <span>{friend.friend_name}</span>
                                            </div>
                                        ))}
                                    </div>
                                </List.Item>
                            )}
                        />
                        </div>
                    </div>
                )}
            </div>
            {/* 右侧展示框 */}
            <div className="display-box">
                <DisplayBox/>  
            </div>
            {/* 搜索结果模态框 */}
            <  SearchResultModal
                visible={searchModalVisible}
                onCancel={() => setSearchModalVisible(false)}
                searchResult={searchResult}
                onApplyFriend={ApplyFriend}
            />
            
        </div>
    );
}


export default Friend;
