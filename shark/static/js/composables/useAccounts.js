const { ref } = Vue;
import { api } from '../modules/api.js';

export function useAccounts(t, showToastMessage) {
    const accounts = ref([]);
    const currentAccount = ref(null);
    const showAddAccountModal = ref(false);
    const newAccountName = ref('');
    const newAccountClientSecret = ref(null);
    const newAccountToken = ref(null);
    const showAccountSuccessModal = ref(false);
    const createdAccountInfo = ref(null);
    const deletingAccountIds = ref(new Set());

    const showUpdateAuthModal = ref(false);
    const updateAuthClientSecret = ref(null);
    const updateAuthToken = ref(null);

    const fetchAccounts = async () => {
         try {
            const res = await api.get('/youtube/accounts');
            accounts.value = res.data;
        } catch (e) {
            console.error(e);
        }
    };

    const handleClientSecretUpload = (event) => {
        newAccountClientSecret.value = event.target.files[0];
    };
    
    const handleTokenUpload = (event) => {
        newAccountToken.value = event.target.files[0];
    };

    const createAccount = async () => {
        if (!newAccountName.value) {
            alert('Please enter a username');
            return;
        }

        const formData = new FormData();
        formData.append('desired_username', newAccountName.value);
        if (newAccountClientSecret.value) {
            formData.append('client_secret_file', newAccountClientSecret.value);
        }
        if (newAccountToken.value) {
            formData.append('token_file', newAccountToken.value);
        }

        try {
            const res = await api.post('/youtube/accounts', formData);
            createdAccountInfo.value = res.data;
            showAddAccountModal.value = false;
            showAccountSuccessModal.value = true;
            newAccountName.value = '';
            newAccountClientSecret.value = null;
            newAccountToken.value = null;
            fetchAccounts();
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.create_account_failed'));
        }
    };

    const copyFtpInfo = (acc) => {
        const info = `Host: ${window.location.hostname}\nPort: 2121\nUser: ${acc.ftp_username}\nPass: ${acc.ftp_password}`;
        navigator.clipboard.writeText(info).then(() => {
            alert('FTP Info copied to clipboard');
        });
    };

    const deleteAccount = async (id, name) => {
        if (!confirm(t('alerts.delete_account_confirm_msg', { name }))) return;
        
        deletingAccountIds.value.add(id);
        try {
            await api.delete(`/youtube/accounts/${id}`);
            showToastMessage(t('alerts.delete_success'));
            await fetchAccounts();
            if (currentAccount.value && currentAccount.value.id === id) {
                currentAccount.value = null;
            }
        } catch (e) {
            alert(e.response?.data?.detail || t('alerts.delete_failed'));
        } finally {
            deletingAccountIds.value.delete(id);
        }
    };

    // Update Auth Logic
    const handleUpdateAuthClientSecretUpload = (event) => {
        updateAuthClientSecret.value = event.target.files[0];
    };
    
    const handleUpdateAuthTokenUpload = (event) => {
        updateAuthToken.value = event.target.files[0];
    };

    const openUpdateAuth = (acc) => {
        currentAccount.value = acc;
        showUpdateAuthModal.value = true;
    };

    const updateAuth = async () => {
        if (!updateAuthClientSecret.value && !updateAuthToken.value) {
            alert('Please select at least one file to update');
            return;
        }
        
        const formData = new FormData();
        if (updateAuthClientSecret.value) {
            formData.append('client_secret_file', updateAuthClientSecret.value);
        }
        if (updateAuthToken.value) {
            formData.append('token_file', updateAuthToken.value);
        }

        try {
            await api.put(`/youtube/accounts/${currentAccount.value.id}/auth`, formData);
            alert('Auth config updated successfully');
            showUpdateAuthModal.value = false;
            updateAuthClientSecret.value = null;
            updateAuthToken.value = null;
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to update auth config');
        }
    };

    return {
        accounts,
        currentAccount,
        showAddAccountModal,
        newAccountName,
        newAccountClientSecret,
        newAccountToken,
        showAccountSuccessModal,
        createdAccountInfo,
        deletingAccountIds,
        showUpdateAuthModal,
        updateAuthClientSecret,
        updateAuthToken,
        fetchAccounts,
        createAccount,
        handleClientSecretUpload,
        handleTokenUpload,
        copyFtpInfo,
        deleteAccount,
        handleUpdateAuthClientSecretUpload,
        handleUpdateAuthTokenUpload,
        openUpdateAuth,
        updateAuth
    };
}
