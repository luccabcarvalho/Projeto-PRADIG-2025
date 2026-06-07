<template>
  <v-container class="auth" fluid>
    <v-row justify="center" align:center class="auth-row">
      <v-col cols="12" sm="1" md="8" lg="10" xl="5" class="d-flex justify-center">
        <v-card class="pa-6 elevation-4 auth-card" style="min-width: 350px;">
          <div class="d-flex flex-column align-center mb-4">
            <v-avatar size="64" color="primary">
              <v-icon color="white">mdi-account</v-icon>
            </v-avatar>
            <h3 class="ma-0">Acesso ao SAMG</h3>
            <small class="grey--text">Entre ou crie sua conta</small>
          </div>

          <v-tabs
            v-model="tab"
            background-color="transparent"
            slider-transition="grow" 
            slider-transition-duration="900"
            slider-color="primary"
            centered
            class="custom-slider-size"
          >
            <v-tab key="login" class="auth-tab">
              Entrar
            </v-tab>
            <v-tab key="register" class="auth-tab">
              Cadastrar
            </v-tab>
          </v-tabs>

          <v-card-text>
            <!-- TAB 0: LOGIN -->
            <div v-if="tab === 0">
              <v-form ref="loginForm" @submit.prevent="submitLogin" lazy-validation>
                <v-text-field
                  v-model="loginData.matricula"
                  label="Matrícula"
                  outlined
                  required
                  class="mb-3"
                />
                <v-text-field
                  v-model="loginData.senha"
                  label="Senha"
                  type="password"
                  outlined
                  required
                  class="mb-3"
                />
              </v-form>

              <v-btn color="primary" class="mt-4" block @click="submitLogin" :loading="loadingLogin">
                Entrar
              </v-btn>

              <v-divider class="my-4" />

              <!-- Botão Google -->
              <div ref="googleBtnContainer" class="d-flex justify-center mb-4 google-btn-container"></div>
            </div>

            <!-- TAB 1: REGISTER -->
            <div v-else>
              <v-form ref="registerForm" @submit.prevent="submitRegister" lazy-validation>
                <v-text-field
                  v-model="registerData.nome"
                  label="Nome Completo"
                  outlined
                  required
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.matricula"
                  label="Matrícula"
                  outlined
                  required
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.email"
                  label="Email"
                  type="email"
                  outlined
                  required
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.senha"
                  label="Senha"
                  type="password"
                  outlined
                  required
                  class="mb-3"
                />
              </v-form>

              <v-btn color="primary" class="mt-4" block @click="submitRegister" :loading="loadingRegister">
                Cadastrar
              </v-btn>
            </div>
          </v-card-text>

          <!-- Mensagens -->
          <v-alert v-if="message" :type="messageType" class="mt-4" dismissible>
            {{ message }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import instance from '@/api/instance';

export default {
  name: 'Auth',
  data() {
    return {
      tab: 0,
      loadingLogin: false,
      loadingRegister: false,
      message: null,
      messageType: 'info',
      loginData: {
        matricula: '',
        senha: '',
      },
      registerData: {
        nome: '',
        matricula: '',
        email: '',
        senha: '',
      },
    };
  },
  mounted() {
    this.initGoogleLogin();
  },
  methods: {
    initGoogleLogin() {
      if (!window.google?.accounts?.id) {
        console.warn('Google Identity Services não carregado');
        return;
      }

      window.google.accounts.id.initialize({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        callback: this.handleGoogleCredential,
      });

      window.google.accounts.id.renderButton(this.$refs.googleBtnContainer, {
        theme: 'outline',
        size: 'large',
        width: '100%',
        text: 'signin_with',
      });
    },

    async handleGoogleCredential(response) {
      this.loadingLogin = true;
      this.message = null;

      try {
        // Envia o token para o backend validar
        const { data } = await instance.post('/auth/google', {
          credential: response.credential,
        });

        this.message = 'Login realizado com sucesso!';
        this.messageType = 'success';

        // Armazena usuário no localStorage
        localStorage.setItem('samg_user', JSON.stringify(data.user));

        // Dispara evento para sincronização
        window.dispatchEvent(
          new CustomEvent('samg_user_changed', { detail: data.user })
        );

        // Aguarda 1.5s e redireciona
        setTimeout(() => {
          this.$router.push({ name: 'inicio' });
        }, 1500);
      } catch (err) {
        this.message = err.response?.data?.error || 'Erro ao fazer login com Google';
        this.messageType = 'error';
      } finally {
        this.loadingLogin = false;
      }
    },

    async submitLogin() {
      if (!this.$refs.loginForm.validate()) return;

      this.loadingLogin = true;
      this.message = null;

      try {
        const { data } = await instance.post('/auth/login', this.loginData);

        this.message = 'Login realizado com sucesso!';
        this.messageType = 'success';

        localStorage.setItem('samg_user', JSON.stringify(data.user));
        window.dispatchEvent(
          new CustomEvent('samg_user_changed', { detail: data.user })
        );

        setTimeout(() => {
          this.$router.push({ name: 'inicio' });
        }, 1500);
      } catch (err) {
        this.message = err.response?.data?.error || 'Erro ao fazer login';
        this.messageType = 'error';
      } finally {
        this.loadingLogin = false;
      }
    },

    async submitRegister() {
      if (!this.$refs.registerForm.validate()) return;

      this.loadingRegister = true;
      this.message = null;

      try {
        await instance.post('/auth/register', this.registerData);

        this.message = 'Cadastro realizado com sucesso! Você pode fazer login agora.';
        this.messageType = 'success';

        this.registerData = { nome: '', matricula: '', email: '', senha: '' };
        this.tab = 0;
      } catch (err) {
        this.message = err.response?.data?.error || 'Erro ao cadastrar';
        this.messageType = 'error';
      } finally {
        this.loadingRegister = false;
      }
    },
  },
};
</script>

<style lang="css" scoped>
.auth {
  background: linear-gradient(135deg, #667eea 0%, 100%);
  min-height: 100vh;
  padding-top: 32px;
  padding-bottom: 32px;
}

.auth-row {
  min-height: calc(50vh - 64px);
}

.auth-card {
  width: 100%;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.google-btn-container {
  width: 100%;
}

.auth-tab {
  min-width: 0 !important; 
  padding: 0 !important; 
  margin: 2px 15% !important; 
  letter-spacing: normal !important;
}

::v-deep(.custom-slider-size .v-tabs-slider-wrapper) {
  display: flex !important;
  justify-content: center !important;
}

::v-deep(.custom-slider-size .v-tabs-slider) {
  width: 75% !important; 
}
.text-grey {
  color: #888;
}
</style>
