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
          </div>

          <v-card-text>
            <div class="d-flex flex-column align-center mb-4">
              <p>Utilize sua conta acadêmica do Google</p>
            </div>
            <div ref="googleBtnContainer" class="d-flex justify-center mb-4 google-btn-container"></div>
          </v-card-text>

              <!-- Dialog para solicitar matrícula após login Google -->
              <v-dialog v-model="showMatriculaDialog" max-width="420">
                <v-card>
                  <v-card-title>Informe sua matrícula</v-card-title>
                  <v-card-text>
                    <v-form ref="matriculaForm" @submit.prevent="enviaMatricula">
                      <v-text-field
                        v-model="matriculaInput"
                        label="Matrícula"
                        outlined
                        required
                      />
                    </v-form>
                  </v-card-text>
                  <v-card-actions>
                    <v-spacer />
                    <v-btn text @click="showMatriculaDialog = false">Cancelar</v-btn>
                    <v-btn color="primary" :loading="loadingMatricula" @click="enviaMatricula">Enviar</v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>

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
      message: null,
      messageType: 'info',
      token: null,
      showMatriculaDialog: false,
      matriculaInput: '',
      loadingMatricula: false,
    };
  },
  mounted() {
    this.iniciaGoogleLogin();
  },
  methods: {
    iniciaGoogleLogin() {
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

        // Armazena usuário e token no localStorage
        localStorage.setItem('samg_user', JSON.stringify(data.user));
        if (data.token) {
          localStorage.setItem('samg_token', data.token);
          this.token = data.token;
        }

        // Dispara evento para sincronização
        window.dispatchEvent(
          new CustomEvent('samg_user_changed', { detail: data.user })
        );

        // Se usuário precisa informar matrícula, abrir diálogo
        if (data.user && data.user.needsMatricula) {
          this.showMatriculaDialog = true;
          this.matriculaInput = '';
          this.loadingLogin = false;
          return;
        }

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

    async enviaMatricula() {
      if (!this.matriculaInput) {
        this.message = 'Informe a matrícula';
        this.messageType = 'error';
        return;
      }

      this.loadingMatricula = true;
      this.message = null;

      try {
        const headers = {};
        if (this.token) headers.Authorization = `Bearer ${this.token}`;

        const { data } = await instance.post(
          '/auth/set-matricula',
          { matricula: this.matriculaInput },
          { headers }
        );

        this.message = 'Matrícula registrada com sucesso!';
        this.messageType = 'success';

        // Atualiza usuário local
        const prevUser = JSON.parse(localStorage.getItem('samg_user') || '{}');
        const user = { ...prevUser, ...data.user };
        localStorage.setItem('samg_user', JSON.stringify(user));
        window.dispatchEvent(new CustomEvent('samg_user_changed', { detail: user }));

        this.showMatriculaDialog = false;
        setTimeout(() => this.$router.push({ name: 'inicio' }), 800);
      } catch (err) {
        this.message = err.response?.data?.error || 'Erro ao enviar matrícula';
        this.messageType = 'error';
      } finally {
        this.loadingMatricula = false;
      }
      this.$router.push('/progresso');
    },

    
  },
};
</script>

<style lang="css" scoped>
.auth {
 
  min-height: 100vh;
  padding-top: 64px;
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
