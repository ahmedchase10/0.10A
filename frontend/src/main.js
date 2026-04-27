import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import './assets/main.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

app.config.errorHandler = (err, _instance, info) => {
    console.error('[Vue error]', info, err);
};

app.mount('#app');