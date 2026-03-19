import { createApp } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'
import lucide from 'lucide'
import './styles.css'

window.Vue = { createApp }
window.axios = axios
window.io = io
window.lucide = lucide

import '../../static/js/app.js'