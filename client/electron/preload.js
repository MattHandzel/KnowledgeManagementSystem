import { contextBridge } from "electron"

contextBridge.exposeInMainWorld("kmd", {
})
