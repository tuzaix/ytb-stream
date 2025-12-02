const { createApp, ref, onMounted, computed, watch } = Vue;
const { createI18n, useI18n } = VueI18n;

const messages = {
    en: {
        app: {
            title: 'Shark YouTube Manager'
        },
        auth: {
            login: 'Login',
            register: 'Register',
            username: 'Username',
            email: 'Email',
            password: 'Password',
            sign_in: 'Sign In',
            create_account: 'Create Account',
            failed: 'Authentication failed'
        },
        nav: {
            dashboard: 'Dashboard',
            memberships: 'Memberships',
            accounts: 'YouTube Accounts',
            logout: 'Logout'
        },
        dashboard: {
            title: 'Dashboard Overview',
            current_plan: 'Current Plan',
            expires: 'Expires: Lifetime',
            accounts_used: 'Accounts Used',
            ftp_storage: 'FTP Storage'
        },
        memberships: {
            title: 'Membership Plans',
            current: 'CURRENT',
            month: '/mo',
            youtube_accounts: 'YouTube Accounts',
            ftp_storage: 'MB FTP Storage',
            ftp_speed: 'Kbps Speed',
            active: 'Active',
            upgrade: 'Upgrade',
            free: 'Free',
            no_membership: 'No Membership'
        },
        membership_levels: {
            normal: { name: 'Normal', description: 'No permissions' },
            silver: { name: 'Silver', description: 'Experience Entry Level' },
            gold: { name: 'Gold', description: 'Personal Practical Level' },
            platinum: { name: 'Platinum', description: 'Advanced Creative Level' },
            diamond: { name: 'Diamond', description: 'Small Team/Enterprise Level' }
        },
        accounts: {
            title: 'YouTube Accounts',
            add_btn: 'Add Account',
            table: {
                account_user: 'Account / FTP User',
                youtube_link: 'YouTube Link',
                status: 'Status',
                actions: 'Actions'
            },
            status: {
                active: 'Active'
            },
            materials_btn: 'Materials',
            schedules_btn: 'Schedules',
            auth_btn: 'Auth Config',
            copy_ftp_btn: 'Copy FTP Info',
            delete_account_btn: 'Delete Account',
            empty: 'No accounts found. Create one to get started.'
        },
        account_details: {
            show: 'Show',
            page: 'Page',
            of: 'of',
            prev: 'Prev',
            next: 'Next',
            yes: 'Yes',
            no: 'No',
            materials_table: {
                group: 'Group',
                type: 'Type',
                templates: 'Templates',
                active: 'Active',
                title_prefix: 'Title:',
                desc_prefix: 'Desc:'
            },
            schedules_table: {
                id: 'ID',
                cron: 'Cron',
                config_id: 'Material Config ID',
                active: 'Active',
                actions: 'Actions'
            }
        },
        cron_builder: {
            type_label: 'Schedule Type',
            types: {
                interval: 'Every X Time',
                daily: 'Daily',
                weekly: 'Weekly',
                monthly: 'Monthly'
            },
            interval_label: 'Run every',
            units: {
                minutes: 'Minutes',
                hours: 'Hours'
            },
            time_label: 'At Time',
            weekdays_label: 'On Days',
            month_day_label: 'On Day of Month',
            preview: 'Schedule:',
            weekdays_items: {
                mon: 'Mon',
                tue: 'Tue',
                wed: 'Wed',
                thu: 'Thu',
                fri: 'Fri',
                sat: 'Sat',
                sun: 'Sun'
            }
        },
        modal: {
            create_account: {
                title: 'Create YouTube/FTP Account',
                placeholder: 'Desired Username'
            },
            update_auth: {
                title: 'Update Auth Config for {name}',
                btn: 'Update Config'
            },
            materials: {
                title: 'Materials for {name}',
                add_title: 'Add New Material Config',
                group_placeholder: 'Group Name (e.g. Fashion)',
                desc_placeholder: 'Description Template',
                tags_placeholder: 'Tags (comma separated)',
                title_template: 'Title Template',
                add_btn: 'Add Material',
                empty: 'No materials configured.'
            },
            schedules: {
                title: 'Schedules for {name}',
                add_title: 'Add Schedule',
                select_config: 'Select Material Config',
                cron_placeholder: 'Cron (e.g. */30 * * * *)',
                create_btn: 'Create Schedule',
                empty: 'No active schedules.',
                config_id: 'Config ID'
            },
            upgrade: {
                title: 'Contact Support to Upgrade',
                instruction: 'Please scan the QR code below to contact customer service for upgrading to {level}.',
                close: 'Close'
            }
        },
        common: {
            cancel: 'Cancel',
            create: 'Create',
            delete: 'Delete',
            shorts: 'Shorts',
            long: 'Long Video'
        },
        alerts: {
            membership_upgraded: 'Membership upgraded!',
            purchase_failed: 'Purchase failed',
            create_account_failed: 'Failed to create account',
            add_material_failed: 'Failed to add material',
            create_schedule_failed: 'Failed to create schedule',
            delete_failed: 'Failed to delete',
            confirm_upgrade: 'Upgrade to {level}?',
            confirm_delete: 'Delete this schedule?',
            delete_account_confirm_msg: 'Are you sure you want to delete account {name}? This action cannot be undone.',
            delete_success: 'Account deleted successfully'
        }
    },
    zh: {
        app: {
            title: 'Shark YouTube 管理后台'
        },
        auth: {
            login: '登录',
            register: '注册',
            username: '用户名',
            email: '邮箱',
            password: '密码',
            sign_in: '登录',
            create_account: '创建账户',
            failed: '认证失败'
        },
        nav: {
            dashboard: '仪表盘',
            memberships: '会员计划',
            accounts: 'YouTube 账号',
            logout: '退出'
        },
        dashboard: {
            title: '仪表盘概览',
            current_plan: '当前计划',
            expires: '有效期：终身',
            accounts_used: '已用账号',
            ftp_storage: 'FTP 存储'
        },
        memberships: {
            title: '会员等级',
            current: '当前等级',
            month: '/月',
            youtube_accounts: 'YouTube 账号',
            ftp_storage: 'MB FTP 存储',
            ftp_speed: 'Kbps 速率',
            active: '当前生效',
            upgrade: '升级',
            free: '免费',
            no_membership: '无会员'
        },
        membership_levels: {
            normal: { name: '普通会员', description: '无权限' },
            silver: { name: '白银会员', description: '入门体验级' },
            gold: { name: '黄金会员', description: '个人实用级' },
            platinum: { name: '白金会员', description: '进阶创作级' },
            diamond: { name: '钻石会员', description: '小型团队/企业级' }
        },
        accounts: {
            title: 'YouTube 账号管理',
            add_btn: '添加账号',
            table: {
                account_user: '账号 / FTP 用户名',
                youtube_link: 'YouTube 链接',
                status: '状态',
                actions: '操作'
            },
            status: {
                active: '活跃'
            },
            materials_btn: '素材配置',
            schedules_btn: '发布计划',
            auth_btn: '应用配置',
            copy_ftp_btn: '复制 FTP 信息',
            delete_account_btn: '删除账号',
            empty: '暂无账号，请创建一个开始使用。'
        },
        account_details: {
            show: '显示',
            page: '页',
            of: '共',
            prev: '上一页',
            next: '下一页',
            yes: '是',
            no: '否',
            materials_table: {
                group: '分组',
                type: '类型',
                templates: '模板',
                active: '激活',
                title_prefix: '标题:',
                desc_prefix: '描述:'
            },
            schedules_table: {
                id: 'ID',
                cron: 'Cron',
                config_id: '配置 ID',
                active: '激活',
                actions: '操作'
            }
        },
        cron_builder: {
            type_label: '调度类型',
            types: {
                interval: '每隔...',
                daily: '每天',
                weekly: '每周',
                monthly: '每月'
            },
            interval_label: '执行间隔',
            units: {
                minutes: '分钟',
                hours: '小时'
            },
            time_label: '执行时间',
            weekdays_label: '选择星期',
            month_day_label: '选择日期',
            preview: '定时执行:',
            weekdays_items: {
                mon: '周一',
                tue: '周二',
                wed: '周三',
                thu: '周四',
                fri: '周五',
                sat: '周六',
                sun: '周日'
            }
        },
        modal: {
            create_account: {
                title: '创建 YouTube/FTP 账号',
                placeholder: '期望的用户名'
            },
            update_auth: {
                title: '{name} 的应用配置更新',
                btn: '更新配置'
            },
            materials: {
                title: '{name} 的素材配置',
                add_title: '添加新素材配置',
                group_placeholder: '分组名称 (例如：时尚)',
                desc_placeholder: '描述模板',
                tags_placeholder: '标签 (逗号分隔)',
                title_template: '标题模板',
                add_btn: '添加素材',
                empty: '暂无素材配置。'
            },
            schedules: {
                title: '{name} 的发布计划',
                add_title: '添加计划',
                select_config: '选择素材配置',
                cron_placeholder: 'Cron 表达式 (例如 */30 * * * *)',
                create_btn: '创建计划',
                empty: '暂无活跃计划。',
                config_id: '配置 ID'
            },
            upgrade: {
                title: '联系客服升级',
                instruction: '请扫描下方二维码添加客服微信，升级至 {level}。',
                close: '关闭'
            }
        },
        common: {
            cancel: '取消',
            create: '创建',
            delete: '删除',
            shorts: '短视频 (Shorts)',
            long: '长视频 (Long)'
        },
        alerts: {
            membership_upgraded: '会员升级成功！',
            purchase_failed: '购买失败',
            create_account_failed: '创建账号失败',
            add_material_failed: '添加素材失败',
            create_schedule_failed: '创建计划失败',
            delete_failed: '删除失败',
            confirm_upgrade: '确定升级到 {level} 吗？',
            confirm_delete: '确定删除该计划吗？',
            delete_account_confirm_msg: '您确定要删除账号 {name} 吗？此操作无法撤销。',
            delete_success: '账号删除成功'
        },
        admin: {
            title: '管理员后台',
            users_title: '用户管理',
            table: {
                id: 'ID',
                username: '用户名',
                email: '邮箱',
                role: '角色',
                membership: '会员等级',
                status: '状态',
                actions: '操作'
            },
            edit_modal: {
                title: '编辑用户',
                role: '角色',
                status: '激活状态',
                membership: '会员等级',
                save: '保存更改'
            }
        }
    }
};

const i18n = createI18n({
    legacy: false, // 关键修复：允许在 setup() 中使用 Composition API
    locale: 'zh', // Default to Chinese
    fallbackLocale: 'en',
    messages,
});

createApp({
    setup() {
        const { t } = useI18n(); // 使用解构出的 useI18n
        
        // State
        const isLoggedIn = ref(false);
        const token = ref(localStorage.getItem('shark_token') || null);
        const user = ref({});
        const authMode = ref('login'); // login or register
        const authForm = ref({ username: '', password: '', email: '' });
        const authError = ref('');
        
        const currentView = ref(localStorage.getItem('shark_current_view') || 'dashboard'); // dashboard, memberships, accounts, admin, account_details
        const currentAccount = ref(null);
        
        const setView = (view) => {
            currentView.value = view;
            localStorage.setItem('shark_current_view', view);
        };

        watch(currentView, (newVal) => {
            localStorage.setItem('shark_current_view', newVal);
        });

        const memberships = ref([]);
        const accounts = ref([]);
        
        // Account Details Pagination State
        const materialsData = ref({ items: [], total: 0, page: 1, pageSize: 5 });
        const schedulesData = ref({ items: [], total: 0, page: 1, pageSize: 10 });
        
        // Modals & Sub-data
        const showAddAccountModal = ref(false);
        const newAccountName = ref('');
        const newAccountClientSecret = ref(null);
        const newAccountToken = ref(null);
        const showAccountSuccessModal = ref(false);
        const createdAccountInfo = ref(null);
        
        const showUpdateAuthModal = ref(false);
        const updateAuthClientSecret = ref(null);
        const updateAuthToken = ref(null);

        // Toast Notification
        const showToast = ref(false);
        const toastMessage = ref('');

        const showToastMessage = (msg) => {
            toastMessage.value = msg;
            showToast.value = true;
            setTimeout(() => {
                showToast.value = false;
            }, 3000);
        };

        // Account Deletion State
        const deletingAccountIds = ref(new Set());

        const showMaterialsModal = ref(false);
        const selectedAccount = ref(null);
        const currentMaterials = ref([]);
        const newMaterial = ref({ group_name: '', material_type: 'shorts', title_template: '', description_template: '', tags: '' });
        
        const showSchedulesModal = ref(false);
        const currentSchedules = ref([]);
        const newSchedule = ref({ material_config_id: '', cron_expression: '' });

        // Cron Builder State
        const scheduleForm = ref({
            type: 'interval', // interval, daily, weekly, monthly
            interval: { value: 30, unit: 'minutes' },
            time: '10:00',
            weekdays: [], // 0-6
            monthDay: 1
        });

        const weekdaysOptions = [
            { value: 1, labelKey: 'mon' },
            { value: 2, labelKey: 'tue' },
            { value: 3, labelKey: 'wed' },
            { value: 4, labelKey: 'thu' },
            { value: 5, labelKey: 'fri' },
            { value: 6, labelKey: 'sat' },
            { value: 0, labelKey: 'sun' }
        ];

        const generateCron = computed(() => {
            const { type, interval, time, weekdays, monthDay } = scheduleForm.value;
            // Parse time HH:MM
            let [hour, minute] = time.split(':').map(Number);
            if (isNaN(hour)) hour = 10;
            if (isNaN(minute)) minute = 0;

            switch (type) {
                case 'interval':
                    if (interval.unit === 'minutes') {
                        // Every N minutes
                        return `*/${interval.value} * * * *`;
                    } else {
                        // Every N hours at minute 0
                        return `0 */${interval.value} * * *`;
                    }
                case 'daily':
                    // At HH:MM every day
                    return `${minute} ${hour} * * *`;
                case 'weekly':
                    // At HH:MM on specific days
                    const days = weekdays.length > 0 ? weekdays.sort().join(',') : '*';
                    return `${minute} ${hour} * * ${days}`;
                case 'monthly':
                    // At HH:MM on specific day of month
                    return `${minute} ${hour} ${monthDay} * *`;
                default:
                    return '*/30 * * * *';
            }
        });

        const formatCron = (cron) => {
            if (!cron) return '-';
            // Simple heuristic parser for display
            if (cron.startsWith('*/')) {
                const parts = cron.split(' ');
                const minPart = parts[0];
                const val = minPart.replace('*/', '');
                return t('cron_builder.types.interval') + ' ' + val + ' ' + t('cron_builder.units.minutes');
            }
            if (cron.startsWith('0 */')) {
                const parts = cron.split(' ');
                const hourPart = parts[1];
                const val = hourPart.replace('*/', '');
                return t('cron_builder.types.interval') + ' ' + val + ' ' + t('cron_builder.units.hours');
            }
            const parts = cron.split(' ');
            if (parts.length === 5) {
                const [m, h, d, mo, w] = parts;
                const time = `${h.padStart(2, '0')}:${m.padStart(2, '0')}`;
                
                if (d === '*' && mo === '*' && w === '*') {
                     return t('cron_builder.types.daily') + ' ' + time;
                }
                if (d === '*' && mo === '*' && w !== '*') {
                     let daysText = w;
                     if (w !== '*') {
                        const dayNums = w.split(',').map(Number);
                        const dayNames = dayNums.map(num => {
                            const opt = weekdaysOptions.find(o => o.value === num);
                            return opt ? t('cron_builder.weekdays_items.' + opt.labelKey) : num;
                        });
                        daysText = dayNames.join(', ');
                     }
                     return t('cron_builder.types.weekly') + ' ' + daysText + ' ' + time;
                }
                if (d !== '*' && mo === '*' && w === '*') {
                     return t('cron_builder.types.monthly') + ' ' + d + ' ' + time;
                }
            }
            return cron;
        };

        // Upgrade Modal
        const showUpgradeModal = ref(false);
        const upgradeLevelName = ref('');

        // Admin State
        const allUsers = ref([]);
        const showEditUserModal = ref(false);
        const editingUser = ref(null);
        const editUserForm = ref({ role: '', is_active: true, membership_level_code: '' });

        // Setup Axios
        const api = axios.create({ baseURL: '' }); // Relative path
        if (token.value) {
            api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
            isLoggedIn.value = true;
        }

        // Actions
        const fetchUser = async () => {
            try {
                const res = await api.get('/users/me');
                user.value = res.data;
            } catch (e) {
                logout();
            }
        };

        const fetchMemberships = async () => {
            const res = await api.get('/users/memberships');
            memberships.value = res.data;
        };

        const fetchAccounts = async () => {
            const res = await api.get('/youtube/accounts');
            accounts.value = res.data;
        };

        const handleAuth = async () => {
            authError.value = '';
            try {
                if (authMode.value === 'register') {
                    await api.post('/auth/register', authForm.value);
                    // Auto login after register
                    authMode.value = 'login';
                    await handleAuth(); // Recurse to login
                    return;
                }
                
                // Login
                const params = new URLSearchParams();
                params.append('username', authForm.value.username);
                params.append('password', authForm.value.password);
                
                const res = await api.post('/auth/login', params);
                token.value = res.data.access_token;
                localStorage.setItem('shark_token', token.value);
                api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
                isLoggedIn.value = true;
                
                await fetchUser();
                await fetchMemberships();
                await fetchAccounts();

            } catch (e) {
                authError.value = e.response?.data?.detail || t('auth.failed');
            }
        };

        const logout = () => {
            token.value = null;
            localStorage.removeItem('shark_token');
            isLoggedIn.value = false;
            user.value = {};
            delete api.defaults.headers.common['Authorization'];
        };

        const purchaseMembership = async (levelCode) => {
            const levelName = t(`membership_levels.${levelCode}.name`);
            // Instead of direct purchase, show modal
            upgradeLevelName.value = levelName;
            showUpgradeModal.value = true;
        };

        const deleteAccount = async (acc) => {
             if (deletingAccountIds.value.has(acc.id)) return;
             if (!confirm(t('alerts.delete_account_confirm_msg', { name: acc.account_name }))) return;
             
             deletingAccountIds.value.add(acc.id);
             try {
                 await api.delete(`/youtube/accounts/${acc.id}`);
                 showToastMessage(t('alerts.delete_success'));
                 // Force save current view state before reload
                 localStorage.setItem('shark_current_view', 'accounts');
                 setTimeout(() => {
                     location.reload();
                 }, 1000);
             } catch (e) {
                 console.error(e);
                 showToastMessage(t('alerts.delete_failed'));
             } finally {
                 deletingAccountIds.value.delete(acc.id);
             }
        };

        const createAccount = async () => {
            if (!newAccountName.value || !newAccountClientSecret.value || !newAccountToken.value) {
                alert(t('alerts.create_account_failed') + ': Missing fields');
                return;
            }
            try {
                const formData = new FormData();
                formData.append('desired_username', newAccountName.value);
                formData.append('client_secret_file', newAccountClientSecret.value);
                formData.append('token_file', newAccountToken.value);

                const res = await api.post('/youtube/accounts', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                createdAccountInfo.value = res.data;
                showAddAccountModal.value = false;
                showAccountSuccessModal.value = true; // Show success modal
                
                newAccountName.value = '';
                newAccountClientSecret.value = null;
                newAccountToken.value = null;
                // Reset file inputs manually if needed, or just let v-if handle it
                
                await fetchAccounts();
            } catch (e) {
                alert(e.response?.data?.detail || t('alerts.create_account_failed'));
            }
        };

        const handleClientSecretUpload = (event) => {
            newAccountClientSecret.value = event.target.files[0];
        };

        const handleTokenUpload = (event) => {
            newAccountToken.value = event.target.files[0];
        };

        const handleUpdateAuthClientSecretUpload = (event) => {
            updateAuthClientSecret.value = event.target.files[0];
        };

        const handleUpdateAuthTokenUpload = (event) => {
            updateAuthToken.value = event.target.files[0];
        };

        const openUpdateAuth = (acc) => {
            selectedAccount.value = acc;
            showUpdateAuthModal.value = true;
            updateAuthClientSecret.value = null;
            updateAuthToken.value = null;
        };

        const updateAuth = async () => {
            if (!selectedAccount.value || !updateAuthClientSecret.value || !updateAuthToken.value) {
                alert('Please select both files');
                return;
            }
            try {
                const formData = new FormData();
                formData.append('client_secret_file', updateAuthClientSecret.value);
                formData.append('token_file', updateAuthToken.value);

                await api.put(`/youtube/accounts/${selectedAccount.value.id}/auth`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                alert('Auth config updated successfully');
                showUpdateAuthModal.value = false;
                updateAuthClientSecret.value = null;
                updateAuthToken.value = null;
            } catch (e) {
                alert(e.response?.data?.detail || 'Failed to update auth config');
            }
        };

        const copyToClipboard = (text) => {
            navigator.clipboard.writeText(text).then(() => {
                showToastMessage('Password copied to clipboard!');
            }).catch(err => {
                console.error('Could not copy text: ', err);
                showToastMessage('Failed to copy password.');
            });
        };

        const copyFtpInfo = (acc) => {
            const info = `IP: ${acc.ftp_host}\nPort: ${acc.ftp_port}\nUser: ${acc.account_name}\nPassword: ${acc.ftp_password}`;
            navigator.clipboard.writeText(info).then(() => {
                showToastMessage('FTP Info copied!');
            }).catch(err => {
                console.error('Could not copy info: ', err);
                showToastMessage('Failed to copy info.');
            });
        };

        // Account Details
        const fetchAccountMaterials = async () => {
            if (!currentAccount.value) return;
            try {
                const offset = (materialsData.value.page - 1) * materialsData.value.pageSize;
                const res = await api.get(`/youtube/accounts/${currentAccount.value.id}/materials?skip=${offset}&limit=${materialsData.value.pageSize}`);
                materialsData.value.items = res.data.items;
                materialsData.value.total = res.data.total;
            } catch (e) {
                console.error(e);
            }
        };

        const fetchAccountSchedules = async () => {
            if (!currentAccount.value) return;
            try {
                const offset = (schedulesData.value.page - 1) * schedulesData.value.pageSize;
                const res = await api.get(`/youtube/accounts/${currentAccount.value.id}/schedules?skip=${offset}&limit=${schedulesData.value.pageSize}`);
                schedulesData.value.items = res.data.items;
                schedulesData.value.total = res.data.total;
            } catch (e) {
                console.error(e);
            }
        };

        const openAccountDetails = async (acc) => {
            currentAccount.value = acc;
            materialsData.value.page = 1;
            schedulesData.value.page = 1;
            await Promise.all([fetchAccountMaterials(), fetchAccountSchedules()]);
            setView('account_details');
        };

        const handleMaterialsPageChange = async (newPage) => {
            if (newPage < 1 || newPage > Math.ceil(materialsData.value.total / materialsData.value.pageSize)) return;
            materialsData.value.page = newPage;
            await fetchAccountMaterials();
        };

        const handleMaterialsPageSizeChange = async () => {
            materialsData.value.page = 1;
            await fetchAccountMaterials();
        };

        const handleSchedulesPageChange = async (newPage) => {
             if (newPage < 1 || newPage > Math.ceil(schedulesData.value.total / schedulesData.value.pageSize)) return;
            schedulesData.value.page = newPage;
            await fetchAccountSchedules();
        };

        const handleSchedulesPageSizeChange = async () => {
            schedulesData.value.page = 1;
            await fetchAccountSchedules();
        };

        const goBackToAccounts = () => {
            currentAccount.value = null;
            setView('accounts');
        };

        // Materials
        const openMaterials = async (acc) => {
            // Deprecated logic compatible with new API, just in case
            selectedAccount.value = acc;
            const res = await api.get(`/youtube/accounts/${acc.id}/materials?skip=0&limit=100`);
            currentMaterials.value = res.data.items;
            showMaterialsModal.value = true;
        };

        const createMaterial = async () => {
            if (!selectedAccount.value && !currentAccount.value) return;
            const accId = selectedAccount.value ? selectedAccount.value.id : currentAccount.value.id;
            
            try {
                await api.post(`/youtube/accounts/${accId}/materials`, newMaterial.value);
                
                if (currentView.value === 'account_details') {
                    // Refresh paginated list
                    await fetchAccountMaterials();
                } else {
                    // Refresh modal list
                    const res = await api.get(`/youtube/accounts/${accId}/materials?skip=0&limit=100`);
                    currentMaterials.value = res.data.items;
                }
                
                // Reset form
                newMaterial.value = { group_name: '', material_type: 'shorts', title_template: '', description_template: '', tags: '' };
                // Close modal if open
                showMaterialsModal.value = false;
            } catch (e) {
                alert(e.response?.data?.detail || t('alerts.add_material_failed'));
            }
        };

        // Schedules
        const openSchedules = async (acc) => {
            selectedAccount.value = acc;
            // We need materials to populate dropdown
            const matRes = await api.get(`/youtube/accounts/${acc.id}/materials?skip=0&limit=100`);
            currentMaterials.value = matRes.data.items;
            
            const res = await api.get(`/youtube/accounts/${acc.id}/schedules?skip=0&limit=100`);
            currentSchedules.value = res.data.items;
            showSchedulesModal.value = true;
        };

        const createSchedule = async () => {
            if (!selectedAccount.value && !currentAccount.value) return;
            const accId = selectedAccount.value ? selectedAccount.value.id : currentAccount.value.id;

            try {
                await api.post(`/youtube/accounts/${accId}/schedules`, {
                    material_config_id: newSchedule.value.material_config_id,
                    cron_expression: generateCron.value,
                    is_active: true
                });
                
                if (currentView.value === 'account_details') {
                    await fetchAccountSchedules();
                } else {
                    const res = await api.get(`/youtube/accounts/${accId}/schedules?skip=0&limit=100`);
                    currentSchedules.value = res.data.items;
                }

                newSchedule.value.cron_expression = '';
                showSchedulesModal.value = false;
            } catch (e) {
                alert(e.response?.data?.detail || t('alerts.create_schedule_failed'));
            }
        };

        const deleteSchedule = async (id) => {
            if (!confirm(t('alerts.confirm_delete'))) return;
            const accId = selectedAccount.value ? selectedAccount.value.id : currentAccount.value.id;

            try {
                await api.delete(`/youtube/schedules/${id}`);
                
                if (currentView.value === 'account_details') {
                    await fetchAccountSchedules();
                } else {
                    const res = await api.get(`/youtube/accounts/${accId}/schedules?skip=0&limit=100`);
                    currentSchedules.value = res.data.items;
                }
            } catch (e) {
                alert(e.response?.data?.detail || t('alerts.delete_failed'));
            }
        };

        // Admin Actions
        const fetchAllUsers = async () => {
            try {
                const res = await api.get('/admin/users');
                allUsers.value = res.data;
            } catch (e) {
                console.error("Failed to fetch users", e);
            }
        };

        const openEditUser = (u) => {
            editingUser.value = u;
            editUserForm.value = {
                role: u.role,
                is_active: u.is_active,
                membership_level_code: u.membership ? u.membership.level_code : 'normal'
            };
            showEditUserModal.value = true;
        };

        const saveUser = async () => {
            if (!editingUser.value) return;
            try {
                await api.put(`/admin/users/${editingUser.value.id}`, editUserForm.value);
                alert('User updated successfully');
                showEditUserModal.value = false;
                fetchAllUsers();
            } catch (e) {
                alert(e.response?.data?.detail || 'Failed to update user');
            }
        };

        const setLocale = (lang) => {
            i18n.global.locale.value = lang; // 在 legacy: false 模式下，locale 是 ref
        };

        // Init
        onMounted(() => {
            if (isLoggedIn.value) {
                fetchUser();
                fetchMemberships();
                fetchAccounts();
            }

            // Safety check: if on account_details but no account selected (e.g. refresh), go back to accounts
            if (currentView.value === 'account_details' && !currentAccount.value) {
                currentView.value = 'accounts';
            }
        });

        return {
            isLoggedIn, authMode, authForm, authError, user, currentView, setView, memberships, accounts,
            handleAuth, logout, purchaseMembership,
            showAddAccountModal, newAccountName, createAccount, handleClientSecretUpload, handleTokenUpload,
            showAccountSuccessModal, createdAccountInfo,
            showUpdateAuthModal, updateAuthClientSecret, updateAuthToken, handleUpdateAuthClientSecretUpload, handleUpdateAuthTokenUpload, openUpdateAuth, updateAuth, copyToClipboard, copyFtpInfo,
            showToast, toastMessage,
            showMaterialsModal, selectedAccount, currentMaterials, newMaterial, openMaterials, createMaterial,
            showSchedulesModal, currentSchedules, newSchedule, openSchedules, createSchedule, deleteSchedule, deleteAccount, deletingAccountIds,
            scheduleForm, generateCron, formatCron, weekdaysOptions,
            // Account Details
            currentAccount,
            materialsData,
            schedulesData,
            openAccountDetails,
            fetchAccountMaterials,
            fetchAccountSchedules,
            handleMaterialsPageChange,
            handleMaterialsPageSizeChange,
            handleSchedulesPageChange,
            handleSchedulesPageSizeChange,
            goBackToAccounts,
            // Admin
            allUsers,
            showEditUserModal,
            editingUser,
            editUserForm,
            fetchAllUsers,
            openEditUser,
            saveUser,
            // Upgrade Modal
            showUpgradeModal,
            upgradeLevelName,
            setLocale,
            // Expose i18n current locale to check active state
            currentLocale: computed(() => i18n.global.locale.value) // 更新 legacy: false 模式下的读取方式
        };
    }
}).use(i18n).mount('#app');
