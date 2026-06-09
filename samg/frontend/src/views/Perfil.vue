<template>
  <v-container class="perfil" fluid>
    <v-row justify="center" align:center style="min-height:60vh;">
      <v-col cols="12" md="6" class="d-flex justify-center">
        <v-card class="pa-6 elevation-2 centered-card">
          <div class="d-flex flex-column align-center mb-4">
            <v-avatar size="64" class="mb-3" color="primary">
              <v-img
                v-if="photoUrl && !photoError"
                :src="photoUrl"
                alt="Foto do perfil"
                contain
                class="profile-photo"
                referrerpolicy="no-referrer"
                @error="photoError = true"
              />
              <v-icon v-else color="white">mdi-account-circle</v-icon>
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
                <v-text-field label="Matrícula" v-model="matriculaValue" />
              </v-col>
            </v-row>

            <v-divider class="my-4" />
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
      
      nameValue: '',
      emailValue: '',
      matriculaValue: '',
      photoUrl: '',
      photoError: false,
      message: null,
      messageType: 'info',
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
    
    loadUser() {
      try {
        const raw = localStorage.getItem('samg_user');
        this.user = raw ? JSON.parse(raw) : null;
      } catch (e) { this.user = null; }

      
      this.nameValue = this.user?.name || '';
      this.emailValue = this.user?.email || '';
      this.matriculaValue = this.user?.matricula || '';
      this.photoUrl = this.user?.fotoPerfil || this.user?.picture || this.user?.photoURL || this.user?.photoUrl || this.user?.avatar || '';
      this.photoError = false;
    },
    
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

.profile-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
</style>