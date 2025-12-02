const { ref } = Vue;
import { api } from '../modules/api.js';

export function useMembership() {
    const memberships = ref([]);
    const showUpgradeModal = ref(false);
    const upgradeLevelName = ref('');

    const fetchMemberships = async () => {
            try {
            const res = await api.get('/users/memberships');
            memberships.value = res.data;
        } catch (e) {
            console.error(e);
        }
    };

    const purchaseMembership = (level) => {
            upgradeLevelName.value = level.name;
            showUpgradeModal.value = true;
    };

    return {
        memberships,
        showUpgradeModal,
        upgradeLevelName,
        fetchMemberships,
        purchaseMembership
    };
}
