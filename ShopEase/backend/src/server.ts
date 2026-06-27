import { Server } from 'http';
import app from './app'
import config from './config';
import { seedAdminAccount } from './helpers/seedAdmin';

async function main() {

    await seedAdminAccount();

    const server: Server = app.listen(config.port, () => {
        console.log("Sever is running on port ", config.port);
    })
}

main();