/**
 * Entry point of the Election app.
 */
import { app, BrowserWindow, Menu, MenuItemConstructorOptions, MenuItem } from 'electron';
import * as path from 'path';
import * as url from 'url';
import treeKill from 'tree-kill';

import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';

/* Splash Screen */
let splashWindow: Electron.BrowserWindow | null;

function openSplashScreen(): void {
    splashWindow = new BrowserWindow({
        height: 300,
        width: 400,
        show: false,
        frame: false,
    });

    splashWindow.loadURL(
        url.format({
            pathname: path.join(__dirname, './splash.html'),
            protocol: 'file:',
            slashes: true,
        })
    );

    splashWindow.once('ready-to-show', () => {
        splashWindow!.show();
    });
}

/* Main Window */
let mainWindow: Electron.BrowserWindow | null;

// Main menu adapted from https://www.electronjs.org/docs/api/menu

function buildMainMenu() {
    const macAppleMenu: MenuItemConstructorOptions = {
        label: 't2wml',
        submenu: [
          { role: 'hide' },
          { role: 'hideothers' },
          { role: 'unhide' },
          { type: 'separator' },
          { role: 'quit' }
        ]
    };
    
    const mainMenuTemplate: MenuItemConstructorOptions[] = [
        {
            label: 'File',
            submenu: [
                isMac() ? { role: 'close' } : { role: 'quit' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'zoomin' },
                { role: 'zoomout' },
                { role: 'resetzoom' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
              ]
        },
        {
            label: 'Debug',
            submenu: [
                { role: 'reload' },
                { role: 'forcereload' },
                { role: 'toggledevtools' },
              ]
        },
    ]

    if (isMac()) {
        mainMenuTemplate.unshift(macAppleMenu);
    }

    const menu = Menu.buildFromTemplate(mainMenuTemplate);
    return menu;
}


function createMainWindow(): void {
    // Create the browser window.
    mainWindow = new BrowserWindow({
        height: 1000,
        width: 1600,
        show: false,
    });

    // and load the index.html of the app.
    mainWindow.loadURL(
        url.format({
            pathname: path.join(__dirname, './index.html'),
            protocol: 'file:',
            slashes: true,
        })
    );

    mainWindow.once('ready-to-show', () => {
        const menu = buildMainMenu();
        Menu.setApplicationMenu(menu);
        mainWindow!.show();
        splashWindow!.close();
        splashWindow = null;
    });
    
    // Emitted when the window is closed.
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}


/* Backend Initialization */
let backendProcess: ChildProcess | null;
let backendUrl = '';

function getBackendPath() {
    let filename = 't2wml-server';
    if (isWindows()) {
        filename = 't2wml-server.exe';
    }
    if (isProd()) {
        return path.join(process.resourcesPath || __dirname, filename);
    }
    return path.join(__dirname, '..', '..', 'backend', 'dist', filename);
}

async function initBackend(): Promise<void> {
    // const port = Math.floor(Math.random() * 20000) + 40000  // Choose a random port between 40000 and 60000
    const port = 13000; // For now the frontend expects the backend to be on port 13000
    const backendPath = getBackendPath();
    console.log(`Spawning backend from ${backendPath}, on port ${port}`);
    try {
        backendProcess = spawn(backendPath, [port.toString()]);
        console.log(`Backend running form ${backendPath} on port ${port}`);
    } catch(err) {
        console.error("Can't run backend: ", err);
        app.quit();
        return;
    }

    backendUrl = `http://localhost:${port}`;
    for(let retryCount=0; retryCount < 120; retryCount++) {
        // Try accessing the backend, see if we get a response
        try {
            await axios.get(`${backendUrl}/api/is-alive`);
            console.log('Backend is ready');
            return;
        } catch(error) {
            await sleep(500); // Wait a bit before trying again
        }
    }

    console.error("Can't open backend");
    app.quit();
}

/* Utilities */
async function sleep(ms: number) {
    return new Promise((resolve) => {
      setTimeout(resolve, ms);
    });
}

function isProd() {
    return process.env.NODE_ENV === 'production';
}

function isMac() {
    return process.platform === 'darwin';
}

function isWindows() {
    return process.platform === 'win32';
}

/* App Initilization */
async function initApp(): Promise<void> {
    openSplashScreen();
    await initBackend();
    
    createMainWindow();  // WIll close the splash window
}

if (!isProd()) {
    app.commandLine.appendSwitch('remote-debugging-port', '9223');
    app.commandLine.appendSwitch('enable-logging');
}

app.once('ready', initApp);

app.on('window-all-closed', async () => {
    // On OS X it is common for applications and their menu bar
    // to stay active until the user quits explicitly with Cmd + Q
    if (!isMac()) {
        app.quit();
    }
});

app.on('activate', () => {
    // On OS X it"s common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (mainWindow === null) {
        createMainWindow();
    }
});

/* Shutting down */
app.on('will-quit', (event) => {
    if (backendProcess) {
        console.log('Killing child process');

        // Killing the backend process takes a little while, we have to
        // wait until it's done before actually quitting, or else on Windows
        // we'll be left with stray server instances.
        treeKill(backendProcess.pid, () => {
            backendProcess = null;
            app.quit();  // Quit for real
        });
        // Prevent quitting until callback is called
        event.preventDefault(); 
    }
});

app.on('quit', () => {
    console.log('t2wml is done');
})
