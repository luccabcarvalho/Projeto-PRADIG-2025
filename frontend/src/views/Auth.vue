<template>
  <v-container class="auth" fluid>
      <v-row justify="center" align="center" style="min-height:100vh;">
      <v-col cols="12" md="6" class="d-flex justify-center">
        <v-card class="pa-6 elevation-4 auth-card">
          <div class="d-flex flex-column align-center mb-4">
            <v-avatar size="64" class="mb-3" color="primary">
              <v-icon color="white">mdi-account</v-icon>
            </v-avatar>
            <h3 class="ma-0">Acesso ao SAMG</h3>
            <small class="grey--text">Entre ou crie sua conta</small>
          </div>

          <v-tabs v-model="tab" background-color="transparent" class="mb-4" grow>
            <v-tab key="login"><v-icon left small>mdi-login</v-icon>Entrar</v-tab>
            <v-tab key="register"><v-icon left small>mdi-account-plus</v-icon>Cadastrar</v-tab>
          </v-tabs>

          <v-card-text>
            <div v-if="tab === 0">
              <v-form ref="loginForm" @submit.prevent="submitLogin" lazy-validation>
                <v-text-field label="Matrícula" v-model="login.matricula" variant="outlined" density="comfortable" :rules="[rules.required, rules.matricula]" prepend-inner-icon="mdi-card-account-details" autofocus required />
                <v-text-field label="Senha" v-model="login.password" :type="showPassword ? 'text' : 'password'" variant="outlined" density="comfortable" :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'" @click:append-inner="showPassword = !showPassword" :rules="[rules.required]" prepend-inner-icon="mdi-lock" required />
                <v-btn color="primary" class="mt-4" block @click="submitLogin">Entrar</v-btn>
              </v-form>
            </div>

            <div v-else>
              <v-form ref="registerForm" @submit.prevent="submitRegister" lazy-validation>
                <v-text-field label="Nome" v-model="register.name" variant="outlined" density="comfortable" :rules="[rules.required]" prepend-inner-icon="mdi-account" required />
                <v-text-field label="Email" v-model="register.email" type="email" variant="outlined" density="comfortable" :rules="[rules.required, rules.email]" prepend-inner-icon="mdi-email" required />
                <v-text-field label="Matrícula" v-model="register.matricula" variant="outlined" density="comfortable" :rules="[rules.required, rules.matricula]" prepend-inner-icon="mdi-card-account-details" required />
                <v-text-field label="Senha" v-model="register.password" :type="showPassword ? 'text' : 'password'" variant="outlined" density="comfortable" :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'" @click:append-inner="showPassword = !showPassword" :rules="[rules.required, rules.min8]" prepend-inner-icon="mdi-lock" required />
                <v-btn color="primary" class="mt-4" block @click="submitRegister">Cadastrar</v-btn>
              </v-form>
            </div>

            <v-alert v-if="message" :type="messageType" class="mt-4" border="left">{{ message }}</v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import instance from '@/api/instance';

export default {
  data() {
    return {
      tab: 0,
      login: { matricula: '', password: '' },
      register: { name: '', email: '', matricula: '', password: '' },
      message: null,
      messageType: 'info',
      showPassword: false,
      rules: {
        required: v => !!v || 'Campo obrigatório',
        email: v => /\S+@\S+\.\S+/.test(v) || 'Email inválido',
        min8: v => (v && v.length >= 8) || 'Use ao menos 8 caracteres',
        matricula: v => (v && /^\d{11}$/.test(v)) || 'Matrícula deve conter exatamente 11 números',
      },
    };
  },
  methods: {
    async submitRegister() {
      this.message = null;
      try {
        const { data } = await instance.post('auth/register', this.register);
        this.message = 'Cadastro realizado com sucesso.';
        this.messageType = 'success';
        
        this.tab = 0;
        this.login.matricula = this.register.matricula;
      } catch (err) {
        this.message = err.response?.data?.error || 'Erro no cadastro';
        this.messageType = 'error';
      }
    },
    async submitLogin() {
      this.message = null;
      try {
        const { data } = await instance.post('auth/login', this.login);
        this.message = 'Login efetuado com sucesso.';
        this.messageType = 'success';
        
        localStorage.setItem('samg_user', JSON.stringify(data.user));
        

        window.dispatchEvent(new CustomEvent('samg_user_changed', { detail: data.user }));
        this.$router.push({ name: 'progresso' });
      } catch (err) {
        this.message = err.response?.data?.error || 'Credenciais incorretas';
        this.messageType = 'error';
      }
    },
  },
};
</script>

<style scoped>
.auth {
  margin-top: 0;
}


.auth-card {
  width: 100%;
  max-width: 32.5rem; 
  box-sizing: border-box;
  margin: 0 auto; 
  min-width: 32.5rem; 
}


@media (max-width: 32.5rem) {
  .auth-card {
    min-width: 0;
    max-width: 22.5rem; 
    padding: 12px;
    margin: 0 auto;
  }
}
</style>
