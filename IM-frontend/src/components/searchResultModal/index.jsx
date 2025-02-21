import React from 'react';
import { Modal, Card, Button } from 'antd';

const SearchResultModal = ({ visible, onCancel, searchResult, onApplyFriend }) => {
    return (
        <Modal
            visible={visible}
            onCancel={onCancel}
            footer={null}
        >
            {searchResult && searchResult.map((user, index) => (
    <Card key={index} title={`搜索用户：${user.user_name}`}>
        {/* 展示搜索结果的基本信息 */}
        <div>{user.user_name}</div>
        <img src={user.user_picture} alt={user.user_name} />
        <Button type="primary" onClick={() => onApplyFriend(user)}>申请添加好友</Button>
    </Card>
))
}
        </Modal>
    );
};

export default SearchResultModal;