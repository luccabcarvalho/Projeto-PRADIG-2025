<template>
  <v-container class="perfil" fluid>
    <v-row justify="center" align="center" style="min-height:60vh;">
      <v-col cols="12" md="6" class="d-flex justify-center">
        <v-card class="pa-6 elevation-2 centered-card">
          <div class="d-flex flex-column align-center mb-4">
            <v-avatar size="64" class="mb-3" color="primary">
              <v-icon color="white">mdi-account-circle</v-icon>
            </v-avatar>
            <h3 class="ma-0">Meu Perfil</h3>
            <small class="grey--text">Visualize e gerencie seus dados</small>
          </div>

          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field label="Nome" v-model="nameValue" readonly />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field label="Email" v-model="emailValue" readonly />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field label="Matrícula" v-model="matriculaValue" readonly />
              </v-col>
            </v-row>

            <v-divider class="my-4" />

            <h4>Alterar senha</h4>
            <v-form ref="pwdForm" lazy-validation>
              <div class="password-input-group">
                <v-text-field label="Senha atual" v-model="oldPassword" :type="showOldPassword ? 'text' : 'password'" variant="outlined" density="comfortable" :rules="[rules.required]" required />
                <button type="button" class="eye-btn" @click="showOldPassword = !showOldPassword" :title="showOldPassword ? 'Ocultar' : 'Mostrar'">
                  <img :src="showOldPassword ? '/src/assets/eyes-open.png' : '/src/assets/eyes-closed.png'" :alt="showOldPassword ? 'Ocultar' : 'Mostrar'" class="eye-img" />
                </button>
              </div>
              <div class="password-input-group">
                <v-text-field label="Nova senha" v-model="newPassword" :type="showNewPassword ? 'text' : 'password'" variant="outlined" density="comfortable" :rules="[rules.required, rules.min8]" required />
                <button type="button" class="eye-btn" @click="showNewPassword = !showNewPassword" :title="showNewPassword ? 'Ocultar' : 'Mostrar'">
                  <img :src="showNewPassword ? '/src/assets/eyes-open.png' : '/src/assets/eyes-closed.png'" :alt="showNewPassword ? 'Ocultar' : 'Mostrar'" class="eye-img" />
                </button>
              </div>
              <div class="password-input-group">
                <v-text-field label="Confirme a nova senha" v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'" variant="outlined" density="comfortable" :rules="[rules.required, matchPassword]" required />
                <button type="button" class="eye-btn" @click="showConfirmPassword = !showConfirmPassword" :title="showConfirmPassword ? 'Ocultar' : 'Mostrar'">
                  <img :src="showConfirmPassword ? '/src/assets/eyes-open.png' : '/src/assets/eyes-closed.png'" :alt="showConfirmPassword ? 'Ocultar' : 'Mostrar'" class="eye-img" />
                </button>
              </div>
              <v-btn color="primary" class="mt-4" :loading="loading" @click="submitChangePassword">Alterar senha</v-btn>
            </v-form>

            <v-alert v-if="message" :type="messageType" class="mt-4">{{ message }}</v-alert>
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
      user: null,
      // local bound fields so inputs update/floating label work reliably
      nameValue: '',
      emailValue: '',
      matriculaValue: '',
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      message: null,
      messageType: 'info',
      loading: false,
      showOldPassword: false,
      showNewPassword: false,
      showConfirmPassword: false,
      rules: {
        required: v => !!v || 'Campo obrigatório',
        min8: v => (v && v.length >= 8) || 'Use ao menos 8 caracteres',
      },
    };
  },
  computed: {
    token() {
      try {
        return this.user?.token || null;
      } catch { return null; }
    }
  },
  methods: {
    matchPassword(v) {
      return (v === this.newPassword) || 'As senhas não coincidem';
    },
    loadUser() {
      try {
        const raw = localStorage.getItem('samg_user');
        this.user = raw ? JSON.parse(raw) : null;
      } catch (e) { this.user = null; }

      // populate the visible inputs from the user object
      this.nameValue = this.user?.name || '';
      this.emailValue = this.user?.email || '';
      this.matriculaValue = this.user?.matricula || '';
    },
    async submitChangePassword() {
      this.message = null;
      if (!this.token) {
        this.message = 'Você precisa estar logado para alterar a senha.';
        this.messageType = 'error';
        return;
      }
      if (!this.oldPassword || !this.newPassword || !this.confirmPassword) {
        this.message = 'Preencha todos os campos.';
        this.messageType = 'error';
        return;
      }
      if (this.newPassword !== this.confirmPassword) {
        this.message = 'As senhas não coincidem.';
        this.messageType = 'error';
        return;
      }
      if (this.newPassword.length < 8) {
        this.message = 'A nova senha precisa ter ao menos 8 caracteres.';
        this.messageType = 'error';
        return;
      }
      this.loading = true;
      try {
        const headers = { Authorization: `Bearer ${this.token}` };
        const { data } = await instance.post('auth/change-password', { oldPassword: this.oldPassword, newPassword: this.newPassword }, { headers });
        this.message = 'Senha alterada com sucesso.';
        this.messageType = 'success';
        this.oldPassword = this.newPassword = this.confirmPassword = '';
        // update local user if needed
        if (data?.user) {
          const updated = Object.assign({}, this.user, { name: data.user.name, email: data.user.email, matricula: data.user.matricula });
          localStorage.setItem('samg_user', JSON.stringify(updated));
          this.loadUser();
          // notify header
          window.dispatchEvent(new CustomEvent('samg_user_changed', { detail: updated }));
        }
      } catch (err) {
        this.message = err.response?.data?.error || (err.message || 'Erro ao alterar senha');
        this.messageType = 'error';
      } finally {
        this.loading = false;
      }
    }
  },
  mounted() {
    this.loadUser();
  }
};
</script>

<style scoped>
.perfil {
  margin-top: 24px;
}

.password-input-group {
  position: relative;
  margin-bottom: 16px;
}

.eye-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  border: none;
  background: none;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eye-img {
  width: 20px;
  height: 20px;
  object-fit: contain;
}
</style>