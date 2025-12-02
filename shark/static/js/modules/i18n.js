import { messages } from './locales.js?v=1.2';

const { createI18n } = VueI18n;

export const i18n = createI18n({
    legacy: false,
    locale: 'zh',
    fallbackLocale: 'en',
    messages,
});
