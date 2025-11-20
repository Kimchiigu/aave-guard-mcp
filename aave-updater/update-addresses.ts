import * as fs from "fs";
import * as path from "path";

// Mainnet Pool
import {
  AaveV3Ethereum,
  AaveV3EthereumEtherFi,
  AaveV3EthereumHorizon,
  AaveV3EthereumLido,
  AaveV3Arbitrum,
  AaveV3Avalanche,
  AaveV3Base,
  AaveV3BNB,
  AaveV3Celo,
  AaveV3Gnosis,
  AaveV3InkWhitelabel,
  AaveV3Linea,
  AaveV3Metis,
  AaveV3Optimism,
  AaveV3Plasma,
  AaveV3Polygon,
  AaveV3Scroll,
  AaveV3Soneium,
  AaveV3Sonic,
  AaveV3ZkSync,
} from "@bgd-labs/aave-address-book";

// Testnet Pool
import {
  AaveV3ArbitrumSepolia,
  AaveV3BaseSepolia,
  AaveV3BaseSepoliaLido,
  AaveV3OptimismSepolia,
  AaveV3ScrollSepolia,
  AaveV3Sepolia,
  AaveV3Fuji,
} from "@bgd-labs/aave-address-book";

const mainnetPools = {
  AaveV3Ethereum,
  AaveV3EthereumEtherFi,
  AaveV3EthereumHorizon,
  AaveV3EthereumLido,
  AaveV3Arbitrum,
  AaveV3Avalanche,
  AaveV3Base,
  AaveV3BNB,
  AaveV3Celo,
  AaveV3Gnosis,
  AaveV3InkWhitelabel,
  AaveV3Linea,
  AaveV3Metis,
  AaveV3Optimism,
  AaveV3Plasma,
  AaveV3Polygon,
  AaveV3Scroll,
  AaveV3Soneium,
  AaveV3Sonic,
  AaveV3ZkSync,
};

const testnetPools = {
  AaveV3ArbitrumSepolia,
  AaveV3BaseSepolia,
  AaveV3BaseSepoliaLido,
  AaveV3OptimismSepolia,
  AaveV3ScrollSepolia,
  AaveV3Sepolia,
  AaveV3Fuji,
};

const allPools = {
  ...mainnetPools,
  ...testnetPools,
};

/**
 * Converting object to JSON String and save to a file
 * @param fileName Output file name (ex: "mainnet.json")
 * @param data JS Object that will be saved
 */
function writeJsonFile(fileName: string, data: object) {
  try {
    const jsonData = JSON.stringify(data, null, 2);
    fs.writeFileSync(path.join(__dirname, fileName), jsonData, "utf-8");
    console.log(`Successfully create: ${fileName}`);
  } catch (error) {
    console.error(`Fail to create ${fileName}:`, error);
  }
}

console.log("Exporting aave addresses to a file...");
writeJsonFile("aave_addresses_mainnet.json", mainnetPools);
writeJsonFile("aave_addresses_testnet.json", testnetPools);
writeJsonFile("aave_addresses_all.json", allPools);
console.log("\nExport finished");
