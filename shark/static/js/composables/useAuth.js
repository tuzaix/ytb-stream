const { ref } = Vue;
import { api } from '../modules/api.js';

export function useAuth(t, setViewCallback) {
    const token = ref(localStorage.getItem('shark_token') || null);
    const isLoggedIn = ref(!!token.value);
    const user = ref({});
    const authMode = ref('login'); // login or register
    const authForm = ref({ username: '', password: '', email: '', totp_code: '' });
    const authError = ref('');
    const is2FARequired = ref(false);

    const fetchUser = async () => {
        try {
            const res = await api.get('/users/me');
            user.value = res.data;
        } catch (e) {
            console.error(e);
        }
    };

    const handleAuth = async (callbacks = {}) => {
        try {
            let res;
            if (authMode.value === 'login') {
                const formData = new FormData();
                formData.append('username', authForm.value.username);
                formData.append('password', authForm.value.password);
                if (authForm.value.totp_code) {
                    formData.append('totp_code', authForm.value.totp_code);
                }
                res = await api.post('/auth/login', formData);
            } else {
                res = await api.post('/auth/register', {
                    username: authForm.value.username,
                    email: authForm.value.email,
                    password: authForm.value.password
                });
                if (res.data) {
                     authMode.value = 'login';
                     alert(t('auth.login') + ' ' + t('auth.please_login'));
                     return;
                }
            }
            
            if (res.data.access_token) {
                token.value = res.data.access_token;
                localStorage.setItem('shark_token', token.value);
                isLoggedIn.value = true;
                is2FARequired.value = false; // Reset
                authForm.value.totp_code = ''; // Clear code
                await fetchUser();
                if (callbacks.onSuccess) callbacks.onSuccess();
            }
        } catch (e) {
            if (e.response?.status === 403 && e.response?.data?.detail === '2FA_REQUIRED') {
                is2FARequired.value = true;
                authError.value = ''; 
                return;
            }
            authError.value = e.response?.data?.detail || t('auth.failed');
        }
    };

    const logout = () => {
        token.value = null;
        localStorage.removeItem('shark_token');
        isLoggedIn.value = false;
        is2FARequired.value = false;
        user.value = {};
        if (setViewCallback) setViewCallback('dashboard');
    };

    return {
        isLoggedIn,
        token,
        user,
        authMode,
        authForm,
        authError,
        is2FARequired,
        handleAuth,
        logout,
        fetchUser
    };
}
