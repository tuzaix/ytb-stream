
// We need to access the logout function or state to handle 401.
// Since we can't easily import logout here without circular dependency if we are not careful.
// We will export a setup function or use a simple event bus or callback.
// For now, we'll just expose the api instance and let the main app configure the interceptors.

export const api = axios.create({
    baseURL: '/api/v1',
});

export const setupApiInterceptors = (token, logoutCallback, forbiddenCallback) => {
    api.interceptors.request.use(config => {
        if (token.value) {
            config.headers.Authorization = `Bearer ${token.value}`;
        }
        return config;
    });

    api.interceptors.response.use(response => response, error => {
        if (error.response) {
            if (error.response.status === 401 && logoutCallback) {
                logoutCallback();
            }
            if (error.response.status === 403 && forbiddenCallback) {
                forbiddenCallback(error.response.data.detail || "Access Denied");
            }
        }
        return Promise.reject(error);
    });
};
