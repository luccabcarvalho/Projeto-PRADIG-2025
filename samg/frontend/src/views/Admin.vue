<template>
  <v-container class="admin-page mt-8">
    <v-row justify="center">
      <v-col cols="12" md="10">
        <h1 class="mb-6 text-center text-h4">Painel de Administração</h1>
        
        
        <v-alert
          v-if="user && user.tipoUsuario !== 'adm'"
          type="error"
          border="left"
          class="mb-6"
        >
          Acesso negado. Apenas administradores podem acessar esta página.
        </v-alert>

        
        <div v-if="user && user.tipoUsuario === 'adm'">
          <v-row class="mb-8">
            <v-col cols="12" md="6">
              <v-card class="pa-6 elevation-4">
                <v-card-title class="text-h6 mb-4">
                  <v-icon left>mdi-book</v-icon>
                  Upload de Currículo
                </v-card-title>

                <v-card-text>
                  <p class="text-sm mb-4">
                    Faça upload de arquivos CSV contendo a definição dos currículos.
                    <br />
                    <strong>Nome do arquivo:</strong> curriculo-NNNNN.csv (ex: curriculo-20232.csv)
                  </p>

                  <v-file-input
                    v-model="curriculoFile"
                    label="Selecionar arquivo CSV"
                    accept=".csv"
                    variant="outlined"
                    class="mb-4"
                  />

                  <v-btn
                    color="primary"
                    block
                    @click="uploadCurriculo"
                    :loading="loadingCurriculo"
                    :disabled="!curriculoFile || loadingCurriculo"
                  >
                    <v-icon left small>mdi-upload</v-icon>
                    Fazer Upload
                  </v-btn>

                  <v-alert
                    v-if="mensagemCurriculo"
                    :type="tipoCurriculo"
                    border="left"
                    class="mt-4"
                  >
                    {{ mensagemCurriculo }}
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="6">
              <v-card class="pa-6 elevation-4">
                <v-card-title class="text-h6 mb-4">
                  <v-icon left>mdi-file-document</v-icon>
                  Upload de Histórico Escolar
                </v-card-title>

                <v-card-text>
                  <p class="text-sm mb-4">
                    Faça upload de arquivos CSV contendo o histórico escolar dos alunos.
                    <br />
                    <strong>Formato esperado:</strong> Dados com matrícula, código, nome e situação das disciplinas.
                  </p>

                  <v-file-input
                    v-model="historicoFile"
                    label="Selecionar arquivo CSV"
                    accept=".csv"
                    variant="outlined"
                    class="mb-4"
                  />

                  <v-btn
                    color="success"
                    block
                    @click="uploadHistorico"
                    :loading="loadingHistorico"
                    :disabled="!historicoFile || loadingHistorico"
                  >
                    <v-icon left small>mdi-upload</v-icon>
                    Fazer Upload
                  </v-btn>

                  <v-alert
                    v-if="mensagemHistorico"
                    :type="tipoHistorico"
                    border="left"
                    class="mt-4"
                  >
                    {{ mensagemHistorico }}
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          
          <v-card class="pa-6 elevation-4">
            <v-card-title class="text-h6 mb-4">
              <v-icon left>mdi-history</v-icon>
              Histórico de Uploads
            </v-card-title>

            <v-card-text>
              <p class="text-sm text-grey">
                Esta seção pode ser expandida para mostrar histórico de uploads realizados.
              </p>
            </v-card-text>
          </v-card>
        </div>

        
        <v-alert
          v-if="!user"
          type="info"
          border="left"
          class="mt-8"
        >
          Para acessar o painel de administração, faça login com uma conta de administrador.
        </v-alert>
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
      curriculoFile: null,
      historicoFile: null,
      loadingCurriculo: false,
      loadingHistorico: false,
      mensagemCurriculo: null,
      mensagemHistorico: null,
      tipoCurriculo: 'info',
      tipoHistorico: 'info',
    };
  },
  methods: {
    loadUser() {
      try {
        const raw = localStorage.getItem('samg_user');
        this.user = raw ? JSON.parse(raw) : null;
        
        
        if (this.user && this.user.tipoUsuario !== 'adm') {
          this.mensagemCurriculo = null;
          this.mensagemHistorico = null;
        }
      } catch (e) {
        this.user = null;
      }
    },

    async uploadCurriculo() {
      if (!this.curriculoFile) return;
      
      this.loadingCurriculo = true;
      this.mensagemCurriculo = null;

      try {
        const formData = new FormData();
        formData.append('pdf', this.curriculoFile);

        const { data } = await instance.post('admin/upload-curriculo', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${this.user.token || ''}`,
          },
        });

        this.mensagemCurriculo = data.mensagem || 'Currículo enviado com sucesso!';
        this.tipoCurriculo = 'success';
        this.curriculoFile = null;

        setTimeout(() => {
          this.mensagemCurriculo = null;
        }, 5000);
      } catch (err) {
        this.mensagemCurriculo = err.response?.data?.error || 'Erro ao fazer upload do currículo';
        this.tipoCurriculo = 'error';
      } finally {
        this.loadingCurriculo = false;
      }
    },

    async uploadHistorico() {
      if (!this.historicoFile) return;

      this.loadingHistorico = true;
      this.mensagemHistorico = null;

      try {
        const formData = new FormData();
        formData.append('pdf', this.historicoFile);

        const { data } = await instance.post('admin/upload-historico', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${this.user.token || ''}`,
          },
        });

        this.mensagemHistorico = data.mensagem || 'Histórico escolar enviado com sucesso!';
        this.tipoHistorico = 'success';
        this.historicoFile = null;

        setTimeout(() => {
          this.mensagemHistorico = null;
        }, 5000);
      } catch (err) {
        this.mensagemHistorico = err.response?.data?.error || 'Erro ao fazer upload do histórico';
        this.tipoHistorico = 'error';
      } finally {
        this.loadingHistorico = false;
      }
    },

    onSamgUserChanged() {
      this.loadUser();
    },
  },
  mounted() {
    this.loadUser();
    window.addEventListener('samg_user_changed', this.onSamgUserChanged);
  },
  beforeUnmount() {
    window.removeEventListener('samg_user_changed', this.onSamgUserChanged);
  },
};
</script>

<style lang="css" scoped>
.admin-page {
  min-height: 100vh;
}

.text-sm {
  font-size: 0.875rem;
}

.text-grey {
  color: #999;
}
</style>
