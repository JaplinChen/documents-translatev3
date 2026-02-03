import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import zhApp from './locales/zh-TW/app.json';
import zhNav from './locales/zh-TW/nav.json';
import zhSidebar from './locales/zh-TW/sidebar.json';
import zhEditor from './locales/zh-TW/editor.json';
import zhComponents from './locales/zh-TW/components.json';
import zhSettings from './locales/zh-TW/settings.json';
import zhCommon from './locales/zh-TW/common.json';
import zhManage from './locales/zh-TW/manage.json';
import zhStatus from './locales/zh-TW/status.json';
import zhLanguage from './locales/zh-TW/language.json';
import zhExport from './locales/zh-TW/export.json';
import zhTermSuggestions from './locales/zh-TW/term_suggestions.json';
import zhUtils from './locales/zh-TW/utils.json';
import zhHistory from './locales/zh-TW/history.json';
import zhApi from './locales/zh-TW/api.json';

import enApp from './locales/en-US/app.json';
import enNav from './locales/en-US/nav.json';
import enSidebar from './locales/en-US/sidebar.json';
import enEditor from './locales/en-US/editor.json';
import enComponents from './locales/en-US/components.json';
import enSettings from './locales/en-US/settings.json';
import enCommon from './locales/en-US/common.json';
import enManage from './locales/en-US/manage.json';
import enStatus from './locales/en-US/status.json';
import enLanguage from './locales/en-US/language.json';
import enExport from './locales/en-US/export.json';
import enTermSuggestions from './locales/en-US/term_suggestions.json';
import enUtils from './locales/en-US/utils.json';
import enHistory from './locales/en-US/history.json';
import enApi from './locales/en-US/api.json';

import viApp from './locales/vi/app.json';
import viNav from './locales/vi/nav.json';
import viSidebar from './locales/vi/sidebar.json';
import viEditor from './locales/vi/editor.json';
import viComponents from './locales/vi/components.json';
import viSettings from './locales/vi/settings.json';
import viCommon from './locales/vi/common.json';
import viManage from './locales/vi/manage.json';
import viStatus from './locales/vi/status.json';
import viLanguage from './locales/vi/language.json';
import viExport from './locales/vi/export.json';
import viTermSuggestions from './locales/vi/term_suggestions.json';
import viUtils from './locales/vi/utils.json';
import viHistory from './locales/vi/history.json';
import viApi from './locales/vi/api.json';

const zhTW = {
    ...zhApp,
    ...zhNav,
    ...zhSidebar,
    ...zhEditor,
    ...zhComponents,
    ...zhSettings,
    ...zhCommon,
    ...zhManage,
    ...zhStatus,
    ...zhLanguage,
    ...zhExport,
    ...zhTermSuggestions,
    ...zhUtils,
    ...zhHistory,
    ...zhApi,
};

const enUS = {
    ...enApp,
    ...enNav,
    ...enSidebar,
    ...enEditor,
    ...enComponents,
    ...enSettings,
    ...enCommon,
    ...enManage,
    ...enStatus,
    ...enLanguage,
    ...enExport,
    ...enTermSuggestions,
    ...enUtils,
    ...enHistory,
    ...enApi,
};

const vi = {
    ...viApp,
    ...viNav,
    ...viSidebar,
    ...viEditor,
    ...viComponents,
    ...viSettings,
    ...viCommon,
    ...viManage,
    ...viStatus,
    ...viLanguage,
    ...viExport,
    ...viTermSuggestions,
    ...viUtils,
    ...viHistory,
    ...viApi,
};

const resources = {
    'zh-TW': { translation: zhTW },
    'zh': { translation: zhTW },
    'en-US': { translation: enUS },
    'en': { translation: enUS },
    'vi': { translation: vi },
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'zh-TW',
        load: 'languageOnly',
        nonExplicitSupportedLngs: true,
        interpolation: {
            escapeValue: false,
        },
        detection: {
            order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
            caches: ['localStorage', 'cookie'],
        },
    });

export default i18n;
