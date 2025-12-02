export const messages = {
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
            expires: 'Expires',
            accounts_used: 'Accounts Used',
            ftp_storage: 'FTP Storage',
            expiration_warning: 'Your membership will expire in {days} days. Please contact the administrator to renew.'
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
                actions: 'Actions',
                title_prefix: 'Title:',
                desc_prefix: 'Desc:'
            },
            schedules_table: {
                cron: 'Schedule',
                config_id: 'Config ID',
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
            delete_material_confirm: 'Are you sure you want to delete this material config? This will also delete all associated schedules. This action cannot be undone.',
            delete_account_confirm_msg: 'Are you sure you want to delete account {name}? This action cannot be undone.',
            delete_success: 'Deleted successfully',
            add_success: 'Added successfully',
            access_denied: 'Access denied or membership expired'
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
            expires: '有效期',
            accounts_used: '已用账号',
            ftp_storage: 'FTP 存储',
            expiration_warning: '您的会员还有 {days} 天到期，请联系管理员续费。'
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
            title: 'YouTube 账号',
            add_btn: '添加账号',
            table: {
                account_user: '账号 / FTP 用户',
                youtube_link: 'YouTube 链接',
                status: '状态',
                actions: '操作'
            },
            status: {
                active: '生效中'
            },
            materials_btn: '素材库',
            schedules_btn: '定时任务',
            auth_btn: '认证配置',
            copy_ftp_btn: '复制 FTP 信息',
            delete_account_btn: '删除账号',
            empty: '暂无账号，请创建一个。'
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
                active: '状态',
                actions: '操作',
                title_prefix: '标题:',
                desc_prefix: '描述:'
            },
            schedules_table: {
                cron: '计划时间',
                config_id: '配置 ID',
                active: '状态',
                actions: '操作'
            }
        },
        cron_builder: {
            type_label: '计划类型',
            types: {
                interval: '每隔 X 时间',
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
            preview: '计划预览:',
            weekdays_items: {
                mon: '一',
                tue: '二',
                wed: '三',
                thu: '四',
                fri: '五',
                sat: '六',
                sun: '日'
            }
        },
        modal: {
            create_account: {
                title: '创建 YouTube/FTP 账号',
                placeholder: '期望的用户名'
            },
            update_auth: {
                title: '更新认证配置 - {name}',
                btn: '更新配置'
            },
            materials: {
                title: '素材管理 - {name}',
                add_title: '添加新素材配置',
                group_placeholder: '分组名称 (如: 时尚)',
                desc_placeholder: '描述模板',
                tags_placeholder: '标签 (逗号分隔)',
                title_template: '标题模板',
                add_btn: '添加素材',
                empty: '暂无素材配置。'
            },
            schedules: {
                title: '任务计划 - {name}',
                add_title: '添加任务',
                select_config: '选择素材配置',
                cron_placeholder: 'Cron 表达式 (如: */30 * * * *)',
                create_btn: '创建任务',
                empty: '暂无活动任务。',
                config_id: '配置 ID'
            },
            upgrade: {
                title: '联系客服升级',
                instruction: '请扫描下方二维码联系客服升级至 {level}。',
                close: '关闭'
            }
        },
        common: {
            cancel: '取消',
            create: '创建',
            delete: '删除',
            shorts: 'Shorts',
            long: '长视频'
        },
        alerts: {
            membership_upgraded: '会员升级成功！',
            purchase_failed: '购买失败',
            create_account_failed: '创建账号失败',
            add_material_failed: '添加素材失败',
            create_schedule_failed: '创建任务失败',
            delete_failed: '删除失败',
            confirm_upgrade: '确认升级至 {level}？',
            confirm_delete: '删除此任务？',
            delete_material_confirm: '确定要删除此素材配置吗？这将同时删除所有关联的任务。此操作不可撤销。',
            delete_account_confirm_msg: '确定要删除账号 {name} 吗？此操作不可撤销。',
            delete_success: '删除成功',
            add_success: '添加成功',
            access_denied: '访问被拒绝或会员已过期'
        }
    }
};