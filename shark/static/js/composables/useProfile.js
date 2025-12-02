const { ref } = Vue;
import { api } from '../modules/api.js';

export function useProfile(t, showToastMessage, fetchUser) {
    const passwordForm = ref({
        old_password: '',
        new_password: '',
        confirm_password: ''
    });
    
    // 2FA Setup State
    const setupData = ref(null); // { secret, provisioning_uri, qr_code_base64 }
    const verifyCode = ref('');
    
    // 2FA Disable State
    const showDisableConfirm = ref(false);
    const disableCode = ref(''); // Password to confirm disable

    const changePassword = async () => {
        if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
            alert(t('profile.password_mismatch') || 'Passwords do not match');
            return;
        }
        
        try {
            await api.post('/auth/change-password', {
                old_password: passwordForm.value.old_password,
                new_password: passwordForm.value.new_password
            });
            showToastMessage(t('profile.password_updated') || 'Password updated successfully');
            passwordForm.value = { old_password: '', new_password: '', confirm_password: '' };
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to update password');
        }
    };

    const setup2FA = async () => {
        try {
            const res = await api.post('/auth/2fa/setup');
            setupData.value = res.data;
            verifyCode.value = '';
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to start 2FA setup');
        }
    };

    const verifyAndEnable2FA = async () => {
        try {
            await api.post('/auth/2fa/verify', { code: verifyCode.value });
            showToastMessage(t('profile.2fa_enabled') || '2FA enabled successfully');
            setupData.value = null;
            if (fetchUser) await fetchUser();
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to verify code');
        }
    };

    const disable2FA = async () => {
        try {
            await api.post('/auth/2fa/disable', { password: disableCode.value });
            showToastMessage(t('profile.2fa_disabled') || '2FA disabled successfully');
            showDisableConfirm.value = false;
            disableCode.value = '';
            if (fetchUser) await fetchUser();
        } catch (e) {
            alert(e.response?.data?.detail || 'Failed to disable 2FA');
        }
    };

    return {
        passwordForm,
        setupData,
        verifyCode,
        showDisableConfirm,
        disableCode,
        changePassword,
        setup2FA,
        verifyAndEnable2FA,
        disable2FA
    };
}
