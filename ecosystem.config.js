module.exports = {
  apps: [
    {
      // 前端应用
      name: 'ai-classroom-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/ai-classroom',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8001'
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      log_file: '/var/log/pm2/ai-classroom-frontend.log',
      out_file: '/var/log/pm2/ai-classroom-frontend-out.log',
      error_file: '/var/log/pm2/ai-classroom-frontend-error.log',
      time: true
    },
    {
      // 后端应用
      name: 'ai-classroom-backend',
      script: 'production_run.py',
      interpreter: 'python3',
      cwd: '/var/www/ai-classroom/backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        PYTHONPATH: '/var/www/ai-classroom/backend',
        HOST: '0.0.0.0',
        PORT: 8001,
        DEBUG: 'False',
        WORKERS: 4
      },
      env_production: {
        PYTHONPATH: '/var/www/ai-classroom/backend',
        HOST: '0.0.0.0',
        PORT: 8001,
        DEBUG: 'False',
        WORKERS: 4
      },
      log_file: '/var/log/pm2/ai-classroom-backend.log',
      out_file: '/var/log/pm2/ai-classroom-backend-out.log',
      error_file: '/var/log/pm2/ai-classroom-backend-error.log',
      time: true
    }
  ],

  // 部署配置
  deploy: {
    production: {
      user: 'root',
      host: 'your-server-ip',
      ref: 'origin/main',
      repo: 'your-git-repository',
      path: '/var/www/ai-classroom',
      'pre-deploy-local': '',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
}; 