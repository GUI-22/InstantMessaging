import React, { useCallback, useEffect, useState } from 'react';
import { Divider, message } from 'antd';
import { useLocalStorageState, useRequest } from 'ahooks';
import styles from './HomePage.module.css';
import Chatbox from './Chatbox';
import { Operations } from './Operations';
import ConversationSelection from './ConversationSelection';
import {
  addConversation,
  joinConversation,
  leaveConversation,
  useMessageListener,
} from '../api/chat';
import { db } from '../api/db';

// 首页组件
const HomePage = () => {
  // 使用localStorage状态管理当前用户(me)和活跃会话ID(activeChat)，页面刷新后可以保持不变
  const [me, setMe] = useLocalStorageState('me', { defaultValue: 'test' });
  const [activeChat, setActiveChat] = useLocalStorageState<number | null>(
    'activeChat',
    { defaultValue: null }
  );
  const { data: conversations, refresh } = useRequest(async () => {
    const convs = await db.conversations.toArray();
    return convs.filter((conv) => conv.members.includes(me!));
  }); // 当前用户的会话列表

  // 本地消息数据最后更新时间，用于触发聊天框的更新
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(0);
  const update = useCallback(() => {
    // 更新函数，从后端拉取消息，合并到本地数据库
    db.pullMessages(me!).then(() => {
      refresh();
      setLastUpdateTime(Date.now());
    });
  }, [me, refresh]);

  useEffect(() => {
    update();
  }, [update]);

  useEffect(() => {
    db.activeConversationId = activeChat || null;
    if (activeChat) {
      db.clearUnreadCount(activeChat).then(refresh);
    }
  }, [activeChat, refresh]);

  useMessageListener(update, me!); // 使用消息监听器钩子，当有新消息时调用更新函数

  return (
    <div className={styles.wrap}>
      <div className={styles.container}>
        <div className={styles.settings}>
          <div className={styles.form}>
            <div className={styles.inputItem}>
              当前用户：
              {me ? ( // 显示当前用户，若未设置则提示
                <strong>{me}</strong>
              ) : (
                <span style={{ color: 'grey' }}>(未设置)</span>
              )}
            </div>
            <div className={`${styles.inputItem} ${styles.hint}`}>
              用户名仅允许字母数字下划线
            </div>
            <Operations // 操作面板组件
              onSwitchUser={(username) => {
                setMe(username);
                setActiveChat(null);
                db.clearCachedData().then(refresh);
              }}
              onNewPrivateChat={async (target) => {
                const conv = await addConversation({
                  type: 'private_chat',
                  members: [me!, target],
                });
                await db.pullConversations([conv.id]);
                setActiveChat(conv.id);
                refresh();
              }}
              onNewGroupChat={async (target) => {
                const conv = await addConversation({
                  type: 'group_chat',
                  members: [me!, ...target],
                });
                await db.pullConversations([conv.id]);
                setActiveChat(conv.id);
                refresh();
              }}
              onJoinGroupChat={async (conversationId) => {
                try {
                  await joinConversation({
                    conversationId,
                    me: me!,
                  });
                  await db.pullMessagesFromConversation(conversationId);
                  await db.pullConversations([conversationId]);
                  setActiveChat(conversationId);
                  refresh();
                  message.success('加入成功');
                } catch (err) {
                  const resp = (err as any).response || {};
                  if (resp.status == 404) {
                    message.error('会话不存在');
                  } else if (resp.status == 403) {
                    message.error('会话不是群聊');
                  }
                }
              }}
              onLeaveGroupChat={async (conversationId) => {
                try {
                  await leaveConversation({
                    conversationId,
                    me: me!,
                  });
                  await db.removeConversations([conversationId]);
                  setActiveChat(null);
                  refresh();
                  message.success('退出成功');
                } catch (err) {
                  const resp = (err as any).response || {};
                  if (resp.status == 404) {
                    message.error('会话不存在');
                  } else if (resp.status == 403) {
                    message.error('会话不是群聊');
                  }
                }
              }}
            />
          </div>
          <Divider className={styles.divider} />
          <div className={styles.conversations}>
            <ConversationSelection // 会话选择组件
              me={me!}
              conversations={conversations || []}
              onSelect={(id) => setActiveChat(id)}
            />
          </div>
        </div>
        <div className={styles.chatBox}>
          <Chatbox // 聊天框组件
            me={me!}
            conversation={
              // 根据活跃会话ID找到对应的会话对象
              activeChat
                ? conversations?.find((item) => item.id === activeChat)
                : undefined
            }
            lastUpdateTime={lastUpdateTime}
          />
        </div>
      </div>
    </div>
  );
};

export default HomePage;
