import { i18n } from './modules/i18n.js';
import { setupApiInterceptors } from './modules/api.js';
import { useAuth } from './composables/useAuth.js';
import { useAccounts } from './composables/useAccounts.js';
import { useMaterials } from './composables/useMaterials.js';
import { useSchedules } from './composables/useSchedules.js';
import { useAdmin } from './composables/useAdmin.js';
import { useMembership } from './composables/useMembership.js';
import { formatCron, weekdaysOptions, copyToClipboard } from './modules/utils.js';

const { createApp, ref, onMounted, computed, watch } = Vue;
const { useI18n } = VueI18n;

createApp({
    setup() {
        const { t } = useI18n();
        
        // Toast Notification (Global)
        const showToast = ref(false);
        const toastMessage = ref('');
        const showToastMessage = (msg) => {
            toastMessage.value = msg;
            showToast.value = true;
            setTimeout(() => { showToast.value = false; }, 3000);
        };

        // Navigation State
        const currentView = ref(localStorage.getItem('shark_current_view') || 'dashboard');
        const setView = (view) => {
            currentView.value = view;
            localStorage.setItem('shark_current_view', view);
        };
        watch(currentView, (newVal) => localStorage.setItem('shark_current_view', newVal));

        // Composables
        const auth = useAuth(t, setView);
        const accounts = useAccounts(t, showToastMessage);
        const membership = useMembership();
        const admin = useAdmin();
        
        // Setup API Interceptors
        setupApiInterceptors(auth.token, auth.logout);

        // Materials
        const materials = useMaterials(t, showToastMessage);
        
        // Schedules
        const schedules = useSchedules(t, showToastMessage, materials.currentMaterials);

        // Account Details Integration
        const openAccountDetails = (acc) => {
            accounts.currentAccount.value = acc;
            setView('account_details');
            materials.selectedMaterialConfigId.value = null;
            materials.handleMaterialsPageSizeChange(acc.id); // Reset page and fetch
            schedules.handleSchedulesPageSizeChange(acc.id, null); // Reset page and fetch
        };

        const goBackToAccounts = () => {
            accounts.currentAccount.value = null;
            setView('accounts');
        };

        // Watch for material group click
        const onClickMaterialGroup = (configId) => {
            if (materials.selectedMaterialConfigId.value === configId) {
                materials.selectedMaterialConfigId.value = null;
            } else {
                materials.selectedMaterialConfigId.value = configId;
            }
            // Reset schedule page and fetch with filter
            schedules.handleSchedulesPageSizeChange(accounts.currentAccount.value.id, materials.selectedMaterialConfigId.value);
        };

        // Wrappers for Create/Delete to pass current context
        const createMaterialWrapper = () => materials.createMaterial(accounts.currentAccount.value?.id);
        const deleteMaterialWrapper = (id) => materials.deleteMaterial(id, accounts.currentAccount.value?.id);
        
        const createScheduleWrapper = async () => {
             const success = await schedules.createSchedule(
                accounts.currentAccount.value?.id, 
                currentView.value
            );
            if (success && currentView.value === 'account_details') {
                schedules.fetchAccountSchedules(accounts.currentAccount.value.id, materials.selectedMaterialConfigId.value);
            }
        };

        const deleteScheduleWrapper = async (id) => {
            const success = await schedules.deleteSchedule(
                id,
                accounts.currentAccount.value?.id,
                currentView.value
            );
             if (success && currentView.value === 'account_details') {
                schedules.fetchAccountSchedules(accounts.currentAccount.value.id, materials.selectedMaterialConfigId.value);
            }
        };
        
        // Pagination wrappers
        const onMaterialsPageChange = (p) => materials.handleMaterialsPageChange(p, accounts.currentAccount.value?.id);
        const onSchedulesPageChange = (p) => schedules.handleSchedulesPageChange(p, accounts.currentAccount.value?.id, materials.selectedMaterialConfigId.value);

        // Init
        onMounted(() => {
            if (auth.isLoggedIn.value) {
                auth.fetchUser();
                membership.fetchMemberships();
                accounts.fetchAccounts();
            }
            
            if (currentView.value === 'account_details' && !accounts.currentAccount.value) {
                setView('accounts');
            }
        });

        return {
            // Auth
            ...auth,
            // Navigation
            currentView,
            setView,
            // Accounts
            ...accounts,
            openAccountDetails,
            goBackToAccounts,
            // Materials
            ...materials,
            createMaterial: createMaterialWrapper,
            deleteMaterial: deleteMaterialWrapper,
            handleMaterialsPageChange: onMaterialsPageChange,
            // Schedules
            ...schedules,
            createSchedule: createScheduleWrapper,
            deleteSchedule: deleteScheduleWrapper,
            handleSchedulesPageChange: onSchedulesPageChange,
            onClickMaterialGroup,
            // Membership
            ...membership,
            // Admin
            ...admin,
            // Utils
            formatCron: (cron) => formatCron(cron, t),
            weekdaysOptions,
            copyToClipboard,
            // Toast
            showToast,
            toastMessage,
            // I18n
            setLocale: (lang) => i18n.global.locale.value = lang,
            currentLocale: computed(() => i18n.global.locale.value)
        };
    }
}).use(i18n).mount('#app');
