import React, { useState, useEffect, useRef } from 'react';
import { apiReqs, getLocalLoginInfo } from '@/api';
import { Card, Button, Modal, Input} from 'antd';
 import Menu from '@mui/material/Menu';
 import MenuItem from '@mui/material/MenuItem';
import IconButton from '@mui/material/IconButton';
import SearchIcon from '@mui/icons-material/Search';
import InfoIcon from '@mui/icons-material/Info'
import DeleteIcon from '@mui/icons-material/Delete';
import CancelIcon from '@mui/icons-material/Cancel';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import { PlusSquareOutlined } from '@ant-design/icons'; // 导入创建图标
import './message.styl'

const Message = () => {
  const [newMessages, setNewMessages] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationList, setConversationList] = useState([]);
  const [conversationChain, setConversationChain] = useState([]);
  const [selectedComponent, setSelectedComponent] = useState('');
  const [friendList, setFriendList] = useState([]);
  const [showFriendList, setShowFriendList] = useState(false);
  const [showGroupInfo, setShowGroupInfo] = useState(false);
  const [conversationMemberList, setConversationMemberList] = useState([]);
  const [readIndex, setReadIndex] = useState(0);

  // unix到普通时间转换器
  function formatUnixTimestamp(unixTimestamp) {
    const date = new Date(unixTimestamp * 1000);
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); 
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}`;
    
    return formattedTime;
  }

  // 获取会话的最大message_id
  function getMaxMessageId(conversationChain) {
    if (!conversationChain || conversationChain.length === 0) {
        return 0;
    }

    // 使用reduce方法找到数组中最大的message_id
    const maxMessageId = conversationChain.reduce((maxId, message) => {
        return Math.max(maxId, message.message_id);
    }, -Infinity); // 初始值设置为负无穷大

    return maxMessageId;
  }

  // 根据 messageId 查找对应的消息内容
  const getReplyMessageById = (replyId) => {
    const replyMessage = conversationChain.find(message => message.message_id === replyId);
    return replyMessage ? replyMessage.message : "未找到回复消息";
  };

  // // 群聊信息展示框
  // function GroupInfoModal({visible, groupName, getFriendList}) {
  //   const [groupMembers, setGroupMembers] = useState([]);

  //   useEffect(() => {
  //     if (conversationMemberList && conversationMemberList.length > 0) {
  //       setGroupMembers(conversationMemberList);
  //     } 
  //   }, [conversationMemberList]);

  //   const [selectedMember, setSelectedMember] = useState(null);
  //   const handleCancel = () => {
  //     setShowGroupInfo(false);
  //   };
  //   const handleTransferOwnership = () => {
  //     apiReqs.transferOwnership({
  //       data: {
  //         conversationId: selectedConversation.conversation_id,
  //         memberId: selectedMember.member_id,
  //       },
  //       success: (res) => {
  //         Modal.success({
  //           title:"成功指定"
  //         });
  //       },
  //       fail: (error) => {
  //         Modal.error({
  //           title: '指定失败',
  //           content: error.message
  //         });
  //       }
  //     });
  //   };
  //   const handleAppointAdmin = () => {
  //     apiReqs.appointAdmin({
  //       data: {
  //         conversationId: selectedConversation.conversation_id,
  //         adminIds: [selectedMember.member_id],
  //       },
  //       success: (res) => {
  //         Modal.success({
  //           title:"成功指定"
  //         });
  //       },
  //       fail: (error) => {
  //         Modal.error({
  //           title: '指定失败',
  //           content: error.message
  //         });
  //       }
  //     });
  //   };
  //   const handleRemoveMember = () => {
  //     apiReqs.removeMember({
  //       data: {
  //         conversationId: selectedConversation.conversation_id,
  //         removeMemberIds: [selectedMember.member_id],
  //       },
  //       success: (res) => {
  //         Modal.success({
  //           title:"成功移除"
  //         });
  //       },
  //       fail: (error) => {
  //         Modal.error({
  //           title: '移除失败',
  //           content: error.message
  //         });
  //       }
  //     });
  //   };
  //   const handleQuitConversation = () => {
  //     apiReqs.quitConversation({
  //       data: {
  //         conversationId: selectedConversation.conversation_id,
  //       },
  //       success: (res) => {
  //         Modal.success({
  //           title:"成功退出群聊"
  //         });
  //       },
  //       fail: (error) => {
  //         Modal.error({
  //           title: '退出失败',
  //           content: error.message
  //         });
  //       }
  //     });
  //   };
  //   return (
  //     <Modal
  //         title={
  //           <>
  //           群聊信息
  //           <button className="icon-button" onClick={getFriendList}>
  //             <PlusSquareOutlined /> {/* 使用创建图标 */}
  //           </button>
  //           </>
  //         }
  //         visible={visible}
  //         onCancel={handleCancel}
  //       >

  //       {/* 群聊名称 */}
  //       <h2>{groupName}</h2>
  
  //       <div className="group-members">
  //         <h3>群成员</h3>
  //         <ul>
  //           {groupMembers.map(member => (
  //             <div key={member.member_id} onClick = {setSelectedMember(member)}>{member.member_name}</div>
  //           ))}
  //         </ul>
  //       </div>
  //       <button onClick={handleQuitConversation}>退出群聊</button>
  //       {/* 操作选项 */}
  //       <Menu
  //         visible={selectedMember !== null}
  //       >
  //         <Menu.Item onClick={handleTransferOwnership}>转让群主</Menu.Item>
  //         <Menu.Item onClick={handleAppointAdmin}>指定为管理员</Menu.Item>
  //         <Menu.Item onClick={handleRemoveMember}>移出群聊</Menu.Item>
  //       </Menu>
  //     </Modal>
  //   );
  // }
  

  // 好友列表模态框
  function FriendListModal({ friendGroups, createConversation,  visible}) {
    const [selectedFriends, setSelectedFriends] = useState([]);
    const [conversationName, setConversationName] = useState("");
  
    const toggleFriendSelection = (friendId) => {
      console.log(friendId);
      if (selectedFriends.includes(friendId)) {
        setSelectedFriends(selectedFriends.filter(id => id !== friendId));
      } else {
        setSelectedFriends([...selectedFriends, friendId]);
      }
    };
  
    const handleOk = () => {
      createConversation(selectedFriends,conversationName);
      setShowFriendList(false);
    };
  
    const handleCancel = () => {
      setShowFriendList(false);
    };
  
    return (
      <div>
        <Modal
          title="创建群聊"
          open={visible}
          onOk={handleOk}
          onCancel={handleCancel}
        >
          <div className="friend-list-container">
            <div 
              style={{
                fontSize:'14px',
                fontWeight:'bold' 
              }}>好友列表</div>
            <div style={{border: "1px solid  #ccc",padding: "10px"}}>
            {friendGroups.map((group, index) => (
              <div key={index} className="friend-group">
                <h3>{group.group_name}</h3>
                <ul>
                  {group.friend_list.map(friend => (
                    <li
                      key={friend.friend_id}
                      onClick={() => toggleFriendSelection(friend.friend_id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                        marginBottom: '10px',
                        color: selectedFriends.includes(friend.friend_id) ? 'blue' : 'inherit',
                      }}
                    >
                      <img
                        src={friend.friend_picture}
                        alt={friend.friend_name}
                        style={{
                          width: '50px',
                          height: '50px',
                          borderRadius: '50%',
                          marginRight: '10px',
                        }}
                      />
                      {friend.friend_name}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            </div>
          </div>
          <input 
              type="text" 
              placeholder="输入群聊名称" 
              value={conversationName}
              onChange={(e) => setConversationName(e.target.value)}
              style={{
                padding: '10px', /* Add padding for spacing */
                borderRadius: '5px', /* Apply border radius for rounded corners */
                border: '1px solid #ccc', /* Add border */
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)', /* Add box shadow for depth */
                fontSize: '14px', /* Set font size */
                width: '100%', /* Set width to fill the container */
                boxSizing: 'border-box', /* Include padding and border in the width */
                outline: 'none', /* Remove default focus outline */
                transition: 'border-color 0.3s ease', /* Add transition effect for border color */
              }}
            />
        </Modal>
      </div>
    );
  }

  // 展示框组件
  function DisplayBox() {
    const [displayedComponent, setDisplayedComponent] = useState(null);
    const [anchorEl, setAnchorEl] = useState(null); // 用于控制菜单显示的锚点元素
    const [anchorElMember, setAnchorElMember] = useState(null); // 用于控制菜单显示的锚点元素
    const [messageForMenu, setMessageForMenu] = useState(null); // 存储要传递给 MenuItem 的消息信息
    const [memberForMenu, setMemberForMenu] = useState(null); // 存储要传递给 MenuItem 的消息信息
    const messageToSend = useRef('');
    const [replyId, setReplyId] = useState(-1);
    const searchCriteria = useRef({
      earliestTime: '',
      memberName: '',
    });
    const [searchResult, setSearchResult] = useState([]);
    const [openModal, setOpenModal] = useState(false);
    const [openInfoModal, setOpenInfoModal] = useState(false);
    const [conversationMemberList, setConversationMemberList] = useState([]);
    const [announcementChain, setAnnouncementChain] = useState([]);
    const newAnnouncement = useRef('');
    const [viewTransferOwnerShip, setViewTransferOwnerShip] = useState(false);
    const [viewAppointAdmin, setViewAppointAdmin] = useState(false);
    const [viewRemoveMember, setViewRemoveMember] = useState(false);
    const [viewApplyChain, setViewApplyChain] = useState(false);
    const [newApplyChain, setNewApplyChain] = useState([]);
    const [friendList, setFriendList] = useState([]);
    const [viewFriendList, setViewFriendList] = useState(false);
    // const chatMessagesRef = useRef(null);

    // // 当 selectedComponent 改变时更新展示的组件
    // useEffect(() => {
    //     const renderComponent = () => { 
    //       return renderChatRecords();  
    //     };

    //     const componentToRender = renderComponent();
    //     setDisplayedComponent(componentToRender);
    // }, [openModal, anchorEl,anchorElMember,replyId,searchResult,openInfoModal,readIndex,conversationMemberList, announcementChain,viewTransferOwnerShip,viewAppointAdmin,viewRemoveMember,viewApplyChain]);


    // 聊天记录展示
    const renderChatRecords = () => {
        if (!selectedConversation) {
          return null;
        };

      // 发送消息
      const sendMessage = () => {
        if (messageToSend.current !== ''){
          apiReqs.sendMessage({
            data: {
              conversationId: selectedConversation.conversation_id,
              message: messageToSend.current,
              replyId: replyId
            },
            success: (res) => {
              messageToSend.current = '';
              // const currentTimeStamp = Math.floor(Date.now() / 1000);
              // // 添加新消息到会话链中
              // const newMessage = {
              //     message_id: res.message_id, // 假设 API 返回消息的 ID
              //     message: messageToSend.current,
              //     sender_name: getLocalLoginInfo().userName,
              //     sender_id: getLocalLoginInfo().userId,
              //     sender_picture: getLocalLoginInfo().picture,
              //     reply_id: replyId,
              //     send_time: currentTimeStamp
              // };
  
              // setConversationChain(prevChain => [...prevChain, newMessage]);
  
              // fetchConversationChain(selectedConversation);
              markReadIndex(selectedConversation.conversation_id,res.message_id)
              setReplyId(-1);
            },
            fail: (error) => {
              Modal.error({
                title: '发送信息失败',
                content: error.message
              });
            }
          });
        }
      };

      // 处理右键点击或鼠标悬停消息
      const handleContextMenu = (event, message) => {
        event.preventDefault(); // 阻止默认右键菜单的显示
        setAnchorEl(event.currentTarget); // 设置菜单显示的位置
        setMessageForMenu(message);
      };

      const handleMemberMenu = (event, member) => {
        event.preventDefault(); // 阻止默认右键菜单的显示
        setAnchorElMember(event.currentTarget); // 设置菜单显示的位置
        setMemberForMenu(member);
      }

      // 处理关闭菜单
      const handleCloseMenu = () => {
          setAnchorEl(null); // 关闭菜单
      };

      const handleCloseMenuMember = () => {
        setAnchorElMember(null); // 关闭菜单
      }

      // 回复消息
      const handleReplyMessage = () => {
        setReplyId(messageForMenu.message_id);
        setAnchorEl(null); // 关闭菜单
        setMessageForMenu(null);
      };

      // 跳转到回复消息的功能
      const handleJumpToReplyMessage = (message) => {
        // 如果replyId不为-1，则滚动到相应的消息处
        if (message.reply_id !== -1) {
            const replyMessageElement = document.getElementById(`message-${message.reply_id}`);
            if (replyMessageElement) {
                replyMessageElement.scrollIntoView({ behavior: "smooth" });
            }
        }
      };

      // useEffect(() => {
      //   const chatMessagesElements = document.getElementsByClassName("chat-messages");
      //   if (chatMessagesElements.length > 0) {
      //     const chatMessagesElement = chatMessagesElements[0]; // 如果有多个元素符合条件，选择第一个元素
      //     chatMessagesElement.scrollTop = chatMessagesElement.scrollHeight;
      //   }
      // }, [conversationChain]);

      const handleJumpToButtom = () => {
        if (readIndex > 0) {
          const chatMessageElement = document.getElementById(`message-${readIndex}`);
          if (chatMessageElement) {
            chatMessageElement.scrollIntoView({ behavior: "instant" });
          }
        }
      }

      useEffect(() => {
        handleJumpToButtom();
      }, [conversationChain]);

      // 辅助信息展示
      const renderAssistInfo = (message) => {
        let reader_list = message.reader_list;
        if (selectedConversation.private === "True") {
          if (message.sender_id !== getLocalLoginInfo().userId)
            return ''
          else
            return reader_list && reader_list.length > 1 ? '已读' : '未读';
        } else {
          return reader_list ? reader_list.map(reader => reader.member_name).join(', ') : '无';
        }
      };

      // 查找聊天记录
      const handleSearchChatRecords = () => {
        console.log("here1")
        console.log(Date.parse(searchCriteria.current.earliestTime) / 1000);
        apiReqs.pullConversationChainHistory({
          data: {
            conversationId: selectedConversation.conversation_id,
            earliestTime:  searchCriteria.current.earliestTime ? Date.parse(searchCriteria.current.earliestTime +  "T00:00:00") / 1000  : 0 ,
            memberName: searchCriteria.current.memberName,
          },
          success: (res) => {
            setSearchResult(res["conversation_chain"]);
          },
          fail: (error) => {
            Modal.error({
              title: '查找聊天记录失败',
              content: error.message
            });
          }
        })
      };


      // 显示查找对话框
      const handleOpenModal = () => {
        setOpenModal(true);
      };

      // 关闭查找对话框
      const handleCloseModal = () => {
        setOpenModal(false);
        setSearchResult([]);
      };

      // 删除聊天记录
      const handleDeleteMessage = (message) => {
        apiReqs.deleteMessage({
          data: {
            messageId:message.message_id
          },
          success: (res) => {
            fetchConversationChain(selectedConversation);
            setAnchorEl(null); // 关闭菜单
            setMessageForMenu(null);
          },
          fail: (error) => {
            Modal.error({
              title: '删除信息失败',
              content: error.message
            });
          }
        });
      };

      const handleOpenInfoModal = () => {
        setOpenInfoModal(true);
      };
      
      const handleOpenGroupInfo = () => {
        apiReqs.pullConversationMemberList({
          data: {
            conversationId:selectedConversation.conversation_id
          },
          success: (res) => {
            setOpenInfoModal(true);
            setConversationMemberList(res["member_list"]);
            setAnnouncementChain(res["announcement_chain"]);
          },
          fail: (error) => {
            Modal.error({
              title: '获取群成员列表失败',
              content: error.message
            });
          }
        });
      };

      const handleTransferOwnership = (members) => {
        apiReqs.transferOwnership({
          data: {
            conversationId: selectedConversation.conversation_id,
            memberId: members[0],
          },
          success: (res) => {
            Modal.success({
              title:"成功指定"
            });
          },
          fail: (error) => {
            Modal.error({
              title: '指定失败',
              content: error.message
            });
          }
        });
      };

      const handleAppointAdmin = (members) => {
        apiReqs.appointAdmin({
          data: {
            conversationId: selectedConversation.conversation_id,
            adminIds: members,
          },
          success: (res) => {
            Modal.success({
              title:"成功指定"
            });
          },
          fail: (error) => {
            Modal.error({
              title: '指定失败',
              content: error.message
            });
          }
        });
      };
      const handleRemoveMember = (members) => {
        apiReqs.removeMember({
          data: {
            conversationId: selectedConversation.conversation_id,
            removeMemberIds: members,
          },
          success: (res) => {
            Modal.success({
              title:"成功移除"
            });
          },
          fail: (error) => {
            Modal.error({
              title: '移除失败',
              content: error.message
            });
          }
        });
      };
      const handleQuitConversation = () => {
        apiReqs.quitConversation({
          data: {
            conversationId: selectedConversation.conversation_id,
          },
          success: (res) => {
            Modal.success({
              title:"成功退出群聊"
            });
          },
          fail: (error) => {
            Modal.error({
              title: '退出失败',
              content: error.message
            });
          }
        });
      };

      const handleAddAnnocement = () => {
        Modal.confirm({
          title: '群公告',
          content: (
              <Input
                  placeholder="请输入新群公告"
                  onChange={(e) => newAnnouncement.current =  e.target.value}
              />
          ),
          onOk: () => {
            console.log('newAnnouncement', newAnnouncement.current)
              apiReqs.putAnnouncement({
                  data: {
                      conversationId: selectedConversation.conversation_id,
                      announcementBody: newAnnouncement.current 
                  },
                  success: (res) => {
                      Modal.success({
                          title: '添加群公告成功',
                          content: '群公告已成功添加'
                      });
                  },
                  fail: (error) => {
                      Modal.error({
                          title: '群公告添加失败',
                          content: error.message
                      });
                  }
              });
          },
          onCancel: () => {
              // 用户取消了输入分组名称，不执行任何操作
          },
      });
      }

      const handlePutAnnouncement = (announcement) => {
        apiReqs.putAnnouncement({
          data: {
            conversationId: selectedConversation.conversation_id,
            announcement:announcement
          },
          success: (res) => {
            Modal.success({
              title:"成功添加群公告"
            });
          },
          fail: (error) => {
            Modal.error({
              title: '添加群公告失败',
              content: error.message
            });
          }
        })
      }

      const handleInfoModalCancel = () => {
        setOpenInfoModal(false);
      }

      const handleViewTransferOwnership = () => {
        setViewTransferOwnerShip(true);
      }
      
      const viewTransferOwnerShipCancel = () => {
        setViewTransferOwnerShip(false);
      }

      function ModalTransferOwnership({ visible, onCancel }){
        const [selectedMembers, setSelectedMembers] = useState([]);
        const handleSelectMember = memberId => {
          setSelectedMembers([memberId]);
        };
      
        return (
          <Modal
            title="转让群主"
            open={visible}
            onCancel={onCancel}
            footer={[
              <Button key="confirm" type="primary" onClick={() => handleTransferOwnership(selectedMembers)} disabled={!selectedMembers}>
                确认
              </Button>,
            ]}
          >
            <ul>
              {conversationMemberList
                .filter(member => member.role !== 'groupOwner') // 过滤出非群主成员
                .map(member => (
                  <li
                    key={member.member_id}
                    onClick={() => handleSelectMember(member.member_id)}
                    style={{
                      cursor: 'pointer',
                      marginBottom: '10px',
                      color: selectedMembers.includes(member.member_id) ? 'blue' : 'inherit',
                    }}
                  >
                    {member.member_name}
                  </li>
                ))}
            </ul>
          </Modal>
        );
      };

      const handleViewAppointAdmin = () => {
        setViewAppointAdmin(true);
      }

      const viewAppointAdminCancel = () => {
        setViewAppointAdmin(false);
      }

      function ModalAppointAdmin({ visible, onCancel }){
        const [selectedMembers, setSelectedMembers] = useState([]);
        
        const handleSelectMember = memberId => {
          if (selectedMembers.includes(memberId)) {
            setSelectedMembers(selectedMembers.filter(id => id !== memberId));
          } else {
            setSelectedMembers([...selectedMembers, memberId]);
          }
        };

        return (
          <Modal
            title="设置管理员"
            open={visible}
            onCancel={onCancel}
            footer={[
              <Button key="confirm" type="primary" onClick={() => handleAppointAdmin(selectedMembers)} disabled={!selectedMembers}>
                确认
              </Button>,
            ]}
          >
            <ul>
              {conversationMemberList
                .filter(member => member.role === 'commonUser')
                .map(member => (
                  <li
                    key={member.member_id}
                    onClick={() => handleSelectMember(member.member_id)}
                    style={{
                      cursor: 'pointer',
                      marginBottom: '10px',
                      color: selectedMembers.includes(member.member_id) ? 'blue' : 'inherit',
                    }}
                  >
                    {member.member_name}
                  </li>
                ))}
            </ul>
          </Modal>
        );
      };

      const handleViewRemoveMember = () => {
        setViewRemoveMember(true);
      }

      const viewRemoveMemberCancel = () => {
        setViewRemoveMember(false);
      }

      function ModalRemoveMember({ visible, onCancel }){
        const [selectedMembers, setSelectedMembers] = useState([]);
        
        const handleSelectMember = memberId => {
          if (selectedMembers.includes(memberId)) {
            setSelectedMembers(selectedMembers.filter(id => id !== memberId));
          } else {
            setSelectedMembers([...selectedMembers, memberId]);
          }
        };

        const isGroupOwner = conversationMemberList.some(member => member.member_id === getLocalLoginInfo().userId && member.role === 'groupOwner');
        const isAdmin = conversationMemberList.some(member => member.member_id === getLocalLoginInfo().userId && member.role === 'admin');

        return (
          <Modal
            title="移除群成员"
            open={visible}
            onCancel={onCancel}
            footer={[
              <Button key="confirm" type="primary" onClick={() => handleRemoveMember(selectedMembers)} disabled={!selectedMembers}>
                确认
              </Button>,
            ]}
          >
            <ul>
              {conversationMemberList
                .filter(member => {
                  if (isGroupOwner) {
                    // 如果本人是群主，则展示除了群主以外的所有成员
                    return member.role !== 'groupOwner';
                  } else if (isAdmin) {
                    // 如果本人是管理员，则只展示普通群成员
                    return member.role === 'commonUser';
                  } else {
                    // 如果本人是普通群成员，则不需要过滤
                    return true;
                  }
                })
                .map(member => (
                  <li
                    key={member.member_id}
                    onClick={() => handleSelectMember(member.member_id)}
                    style={{
                      cursor: 'pointer',
                      marginBottom: '10px',
                      color: selectedMembers.includes(member.member_id) ? 'blue' : 'inherit',
                    }}
                  >
                    {member.member_name}
                  </li>
                ))}
            </ul>
          </Modal>
        );
        
      };

      const handleViewApplyChain = () => {
        apiReqs.pullConversationApplyChain({
          data: {
            conversationId: selectedConversation.conversation_id
          },
          success: (res) => {
              setNewApplyChain(res["total_conversation_apply_chain"]);
          },
          fail: (error) => {
              Modal.error({
                  title: '拉取入群申请失败',
                  content: error.message
              })
          }
        });
        setViewApplyChain(true);
      }

      const viewApplyChainCancel = () => {
        setViewApplyChain(false);
      }

      function ModalApplyChain({ visible, onCancel }){
        const handleSelectMember = memberId => {
          if (selectedMembers.includes(memberId)) {
            setSelectedMembers(selectedMembers.filter(id => id !== memberId));
          } else {
            setSelectedMembers([...selectedMembers, memberId]);
          }
        };

        const handleGroupRequest = (apply, conversationId, agree) => {
          apiReqs.handleConversationApply(
              {
                  data: {
                      conversationId: conversationId,
                      invitedUserIds: [apply.invited_user_id],
                      agree: agree
                  },
                  success: (res) => {
                      if (agree === "True") {
                          Modal.success({
                              title: '成功同意',
                              content: `成功同意 ${apply.invited_user_name} 入群`
                          });
                          handleViewApplyChain();
                      } else {
                          Modal.success({
                              title: '成功拒绝',
                              content: `成功拒绝 ${apply.invited_user_name} 入群`
                          });
                          handleViewApplyChain();
                      }
                  },
                  fail: (error) => {
                      Modal.error({
                          title: '处理失败',
                          content: error.message
                      });
                  }
              }
          );
      }
      
        return (
          <Modal
            title="入群申请"
            open={visible}
            onCancel={onCancel}
          >
            {newApplyChain.length > 0 && (
                    <Card style={{ width: '100%' }}>
                      {newApplyChain.map(group => (
                        <div key={group.conversation_id} style={{ marginBottom: '10px' }}>
                          <h4>{group.conversation_name}</h4>
                          {group.conversation_apply_chain.map(apply => (
                            <div key={`${apply.invitor_user_id}-${apply.invited_user_id}`} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                              <span style={{ marginRight: '10px' }}>{apply.invited_user_name} 申请加入</span>
                              <span>邀请人：{apply.invitor_user_name}</span>
                              <Button type="primary" onClick={() => handleGroupRequest(apply,group.conversation_id,"True")} style={{marginLeft:'10px',marginRight:'20px'}}>同意</Button>
                              <Button type="primary" danger onClick={() => handleGroupRequest(apply,group.conversation_id,"False")}>拒绝</Button>
                            </div>
                          ))}
                        </div>
                      ))}
                    </Card>
                  )}
          </Modal>
        );
      }

      const handleViewFriendList = () => {
        apiReqs.pullFriendList({
          success: (res) => {
            setFriendList(res);
            setViewFriendList(true);
          },
          fail: (error) => {
            Modal.error({
                title: '拉取好友列表失败',
                content: error.message
            });
          }
        })
      }

      const viewFriendListCancel = () => {
        setViewFriendList(false);
      }

      function ModalFriendList({ visible, onCancel}) {
        const [selectedFriends, setSelectedFriends] = useState([]);
      
        const toggleFriendSelection = (friendId) => {
          console.log(friendId);
          if (selectedFriends.includes(friendId)) {
            setSelectedFriends(selectedFriends.filter(id => id !== friendId));
          } else {
            setSelectedFriends([...selectedFriends, friendId]);
          }
        };
      
        const handleOk = () => {
          inviteFriend(selectedFriends);
          setViewFriendList(false);
        }
     
        return (
          <div>
            <Modal
              title="邀请好友"
              open={visible}
              footer={[
                <Button key="confirm" type="primary" onClick={handleOk} disabled={!selectedFriends}>
                  确认
                </Button>,
              ]}
              onCancel={onCancel}
            >
              <div className="friend-list-container">
                {friendList.map((group, index) => (
                  <div key={index} className="friend-group">
                    <h3>{group.group_name}</h3>
                    <ul>
                      {group.friend_list.filter(friend => conversationMemberList.some(member => member.friend_id !== friend.friend_id)).map(friend => (
                        <li
                          key={friend.friend_id}
                          onClick={() => toggleFriendSelection(friend.friend_id)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            cursor: 'pointer',
                            marginBottom: '10px',
                            color: selectedFriends.includes(friend.friend_id) ? 'blue' : 'inherit',
                          }}
                        >
                          <img
                            src={friend.friend_picture}
                            alt={friend.friend_name}
                            style={{
                              width: '50px',
                              height: '50px',
                              borderRadius: '50%',
                              marginRight: '10px',
                            }}
                          />
                          {friend.friend_name}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Modal>
          </div>
        );
      }

      // 处理按下回车键的事件
      const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault(); // 防止默认的回车行为（例如换行）
          if (messageToSend.current !== ''){
            sendMessage();
          }
        }
      };

      return (
        <div className="chat-records" style={{ marginLeft:'10px', height: '100%', flexDirection: 'column' }}>
            {/* 显示会话名并提供功能icon */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px' }}>
                <h2>{selectedConversation.conversation_name}</h2>
                {/* 查找 */}
                <IconButton onClick={handleOpenModal}>
                    <SearchIcon />
                </IconButton>
                {/* 展示群聊信息 */}
                {selectedConversation.private !== "True" && (
                  <IconButton onClick={handleOpenGroupInfo}>
                    <InfoIcon />
                  </IconButton>
                )}
            </div>
            <div className="chat-messages">
              {conversationChain.map((message, index) => (
                <div key={message.message_id} id={`message-${message.message_id}`} className={`message-container ${message.sender_id === getLocalLoginInfo().userId ? 'own-message' : 'other-message'}`}
                  onContextMenu={(e) => handleContextMenu(e, message)} // 添加右键点击或鼠标悬停事件
                  onClick={() => handleJumpToReplyMessage(message)} // 添加点击事件处理程序
                >
                  <div className="avatar">
                    <img src={message.sender_picture} alt={message.sender_name} />
                  </div>
                  <div className="message-content" style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div className="assist-message">
                      <span className='time'>{formatUnixTimestamp(message.send_time)}</span>
                      {renderAssistInfo(message)}
                    </div>
                    <div className='message-info'style={{width:'fit-content',height:'42px'}}>
                      <p>{message.message}</p>
                    </div>
                    {message.reply_id !== -1 && (
                      <div className="reply-message" style={{fontSize:'13px'}}>
                        <p>{message.sender_name}: {getReplyMessageById(message.reply_id)}</p>
                      </div>
                    )}
                    {message.reply_count !== 0 && (
                      <div className="reply-count" style={{fontSize:'13px'}}>
                        <p>被回复数：{message.reply_count}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* 发送信息的输入框和按钮 */}
            <div className='message-input-container'>
              <div className="message-input"  style={{ marginTop: '20px' }}>
                <input
                  type="text"
                  onChange={(e) => messageToSend.current = e.target.value}
                  onKeyDown={handleKeyDown} // 监听键盘事件
                />
                <button onClick={sendMessage}>发送</button>
              </div>
              {/* 显示要回复的消息 */}
              {replyId !== -1 && (
                <div className="reply-message">
                  <div className="reply-content">
                    <p>回复：{getReplyMessageById(replyId)}</p>
                  </div>
                  <div className="cancel-button" onClick={() => setReplyId(-1)}>
                    <CancelIcon />
                  </div>
              </div>
              )}
            </div>

            {/* 拓展列表 */}
            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleCloseMenu}
            >
                <MenuItem onClick={handleReplyMessage}>回复消息</MenuItem>
                <MenuItem onClick={() => handleDeleteMessage(messageForMenu)}>删除消息</MenuItem>
            </Menu>

            {/* Modal dialog for search criteria */}
            <Modal open={openModal} 
              onOk={handleSearchChatRecords}
              onCancel={handleCloseModal}
            >
                <div  style={{ padding: '20px' }}>
                    <Typography variant="h6">查找聊天记录</Typography>
                    {/* Input fields for search criteria */}
                    <Input
                      label="发送时间"
                      placeholder='发送时间：'
                      onChange={(e) => searchCriteria.current.earliestTime = e.target.value} 
                    />
                    <Input
                        label="发送人"
                        placeholder='发送人：'
                        onChange={(e) => searchCriteria.current.memberName = e.target.value}
                    />
                </div>
                {searchResult.length > 0 && (
                  <div style={{ marginTop: '20px', maxHeight: '300px', overflowY: 'auto', padding: '10px', border: '1px solid #ccc' }}>
                    <Typography variant="h6">查找结果：</Typography>
                    {searchResult.map((message) => (
                      <div key={message.message_id} style={{ marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                          <p style={{ marginBottom: '5px' }}>{message.message}</p>
                          <p style={{ fontSize: '12px', color: '#999', marginBottom: '5px' }}>发送时间：{formatUnixTimestamp(message.send_time)}</p>
                          <p style={{ fontSize: '12px', color: '#999' }}>发送用户：{message.sender_name}</p>
                      </div>
                    ))}
                </div>
                )}
            </Modal>

            <Modal
              title={
                <>
                  群聊信息
                  <button className="icon-button" style={{marginLeft: '10px'}} onClick={handleViewFriendList}>
                    <PlusSquareOutlined /> {/* 使用创建图标 */}
                  </button>
                </>
              }
              open={openInfoModal}
              onCancel={handleInfoModalCancel}
            >
              <h2>群名称：{selectedConversation.conversation_name}</h2>

              <div className="group-members">
                <h3 style={{ marginBottom: '10px' }}>群成员</h3>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {conversationMemberList.map(member => (
                    <li
                      key={member.member_id}
                      id={`member-${member.member_id}`}
                      style={{
                        marginBottom: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer'
                      }}
                      onContextMenu={(e) => handleMemberMenu(e, member)}
                    >
                      <img
                        src={member.member_picture}
                        alt={member.member_name}
                        style={{
                          width: '50px',
                          height: '50px',
                          borderRadius: '50%',
                          marginRight: '10px'
                        }}
                      />
                      <span>{member.member_name}</span>
                      <span style={{ marginLeft: '10px' }}>
                        {member.role === 'groupOwner' ? '群主' : member.role === 'admin' ? '管理员' : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              {announcementChain.length > 0 && (
                <div className="group-announcement">
                  <h3 style={{ marginBottom: '10px' }}>群公告</h3>
                  {announcementChain.map(announcement => (
                    <div
                      key={announcement.announcement_id}
                      style={{ marginBottom: '10px' }}
                    >
                      <p>{announcement.announcement_body}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="group-buttons">
                <button onClick={handleAddAnnocement}>添加群公告</button>
                <button onClick={handleQuitConversation}>退出群聊</button>
                {conversationMemberList.find(member => member.member_id === getLocalLoginInfo().userId && member.role === 'groupOwner') && (
                  <>
                    <button onClick={handleViewTransferOwnership}>转让群主</button>
                    <button onClick={handleViewAppointAdmin}>设置管理员</button>
                    <button onClick={handleViewRemoveMember}>移除群成员</button>
                    <button onClick={handleViewApplyChain}>查看入群申请</button>
                    </>
                )}
                {conversationMemberList.find(member => member.member_id === getLocalLoginInfo().userId && member.role === 'admin') && (
                  <>
                    <button onClick={handleViewRemoveMember}>移除群成员</button>
                    <button onClick={handleViewApplyChain}>查看入群申请</button>
                  </>
                )}
              </div>
            </Modal>

            <ModalTransferOwnership
              visible={viewTransferOwnerShip}
              onCancel={viewTransferOwnerShipCancel}
            />

            <ModalAppointAdmin
              visible={viewAppointAdmin}
              onCancel={viewAppointAdminCancel}
            />

            <ModalRemoveMember
              visible={viewRemoveMember}
              onCancel={viewRemoveMemberCancel}
            />

            <ModalApplyChain
              visible={viewApplyChain}
              onCancel={viewApplyChainCancel}
            />

            <ModalFriendList
              visible={viewFriendList}
              onCancel={viewFriendListCancel}
            />
        </div>
    );
  };
  // 返回展示的组件
  return renderChatRecords(); ;
}

  // // 获取新消息
  // const fetchNewMessages = () => {
  //   fetchConversationList();
  //   fetchConversationChain();
  //   apiReqs.pullUserChain({
  //     success: (res) => {
  //       setNewMessages(res);
  //       // Update conversation list with unread message count
  //       updateConversationList(newMessages);
  //     },
  //     fail: (error) => {
  //       Modal.error({
  //         title: '获取新消息失败',
  //         content: error.message
  //     });
  //     }
  //   })
  // };

  // Update conversation list with unread message count
  const updateConversationList = (messages) => {
    messages.forEach(newMessage => {
      const targetConversation = conversationList.find(chat => chat.conversation_id === newMessage.conversation_id);
      if (targetConversation) {
        targetConversation.unread_count += 1;
      }
    });
    selectedConversation.unread_count = 0;
    setConversationList([...conversationList]);
  };

  // // 每隔一段时间获取新消息
  // useEffect(() => {
  //   const intervalId = setInterval(() => {
  //     fetchConversationList();
  //   }, 10000); // Fetch every 1 minute (adjust as needed)

  //   // Cleanup function to clear interval on component unmount
  //   return () => clearInterval(intervalId);
  // }, []); // Empty dependency array ensures the effect runs only once on mount

  // 登录时获取会话列表
  const fetchConversationList = () => {
    apiReqs.pullConversationList({
      success: (res) => {
        setConversationList(res["conversation_list"]);
      },
      fail: (error) => {
        Modal.error({
          title: '获取会话列表失败',
          content: error.message
        });
      } 
    })
  };

  useEffect(() => {
    fetchConversationList();
    if (selectedConversation) {
      fetchConversationChain(selectedConversation);
    }
  }, [readIndex]); // 空数组作为依赖，表示只在首次渲染时调用


  // 点击事件：选择会话
  const handleConversationSelection = (conversation) => {
    setSelectedConversation(conversation);
    conversation.unread_count = 0;
    apiReqs.pullConversationChain({
      data: {
        conversationId: conversation.conversation_id
      },
      success: (res) => {
        const maxMessageId = getMaxMessageId(res["conversation_chain"]);
        markReadIndex(conversation.conversation_id, maxMessageId);  
        // const maxMessageId = getMaxMessageId(res["conversation_chain"]);
        // console.log("maxMessageId:", maxMessageId);
        // markReadIndex(chat.conversation_id, maxMessageId);
        setConversationChain(res["conversation_chain"])
      },
      fail: (error) => {
        Modal.error({
          title: '获取会话链失败',
          content: error.message
        });
      }
    });
  };

  // 获取会话链
  const fetchConversationChain = (chat) => {
    apiReqs.pullConversationChain({
      data: {
        conversationId: chat.conversation_id
      },
      success: (res) => {
        setConversationChain(res["conversation_chain"]);
        // const maxMessageId = getMaxMessageId(res["conversation_chain"]);
        // console.log("maxMessageId:", maxMessageId);
        // markReadIndex(chat.conversation_id, maxMessageId);
      },
      fail: (error) => {
        Modal.error({
          title: '获取会话链失败',
          content: error.message
        });
      }
    });
  };

  // 标记read_index
  const markReadIndex = (conversationId, maxMessageId) => {
    apiReqs.markReadIndex({
      data: {
        conversationId: conversationId,
        readIndex: maxMessageId
      },  
      success: (res) => {
        console.log("标记会话read_index成功");
        setReadIndex(maxMessageId);
      },
      fail: (error) => {
        Modal.error({
          title: '标记会话read_index失败',
          content: error.message
        });
      }
    });
  };
  

  const createConversation = (friendIds,conversationName) => {
    console.log("here")
    console.log(friendIds);
    console.log(conversationName);
    apiReqs.createConversation({
      data: {
        conversationName: conversationName,
        friendIds:friendIds
      },
      success: (res) => {
        Modal.success({
          title: '创建会话成功',
          content: `会话ID: ${res.conversation_id}`
          });
          fetchConversationList();
          setSelectedConversation(res);
      },
      fail: (error) => {
        Modal.error({
          title: '创建会话失败',
          content: error.message
        });
      }
    })
  };

  const inviteFriend = (friendIds) => {
    apiReqs.inviteNewMember({
      data: {
        conversationId: selectedConversation.conversation_id,
        newMemberIds:friendIds
      },
      success: (res) => {
        Modal.success({
          title: '邀请成功',
          });
      },
      fail: (error) => {
        Modal.error({
          title: '创建会话失败',
          content: error.message
        });
      }
    });
  }

   // 获取好友列表
   const getFriendList = () => {
    apiReqs.pullFriendList({
        success: (res) => {
            setFriendList(res);
            setShowFriendList(true);
        },
        fail: (error) => {
            Modal.error({
                title: '拉取好友列表失败',
                content: error.message
            });
        }
    });
  };

  return (
    <div className="message-container">
      {/* 左侧会话管理列表 */}
      <div className="message-list">
        <header className="list-header">
          <div className="search-box">
            <input type="text" placeholder="搜索" />
          </div>
          <button className="icon-button" onClick={getFriendList}>
            <PlusSquareOutlined /> {/* 使用创建图标 */}
          </button>
        </header>
        {/* <button className="fetch-button" onClick={fetchNewMessages}>获取新消息</button> */}
          <ul>
            {conversationList.map((chat) => (
              <li key={chat.conversation_id} onClick={() => handleConversationSelection(chat)}>
                <span>{chat.conversation_name}</span> {/* 显示会话名称 */}
                {chat.unread_count > 0 && (
                  <span className="unread-count">
                    未读消息数：{chat.unread_count}
                  </span>
                )} {/* 显示未读消息数 */}
              </li>
            ))}
          </ul>
      </div>
      {/* 右侧展示框 */}
      <div className="display-box">
        <DisplayBox/>  
      </div>
      {/* 右侧展示群基本信息 */}
      <div className='friend-list'>
        <FriendListModal
          key={showFriendList}
          visible={showFriendList}
          friendGroups={friendList}
          createConversation={createConversation}
        />
      </div>
    </div>
  );
  
};

export default Message;
