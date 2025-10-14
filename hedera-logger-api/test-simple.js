const { Client, PrivateKey, TopicMessageSubmitTransaction } = require("@hashgraph/sdk");
require("dotenv").config();

async function testHederaLogging() {
  console.log("🧪 Testing Hedera logging directly...");

  try {
    const accountId = process.env.HEDERA_ACCOUNT_ID;
    const privateKeyStr = process.env.HEDERA_PRIVATE_KEY;
    const topicId = process.env.HEDERA_TOPIC_ID;

    console.log("Environment check:");
    console.log("- Account ID:", accountId ? "✅ Set" : "❌ Missing");
    console.log("- Private Key:", privateKeyStr ? "✅ Set" : "❌ Missing");
    console.log("- Topic ID:", topicId ? "✅ Set" : "❌ Missing");

    if (!accountId || !privateKeyStr || !topicId) {
      throw new Error("Missing required environment variables");
    }

    const privateKey = PrivateKey.fromString(privateKeyStr);
    const client = Client.forTestnet();
    client.setOperator(accountId, privateKey);

    const testMessage = `Local test message at ${new Date().toISOString()}`;
    console.log("\n📤 Sending message:", testMessage);

    const tx = await new TopicMessageSubmitTransaction()
      .setTopicId(topicId)
      .setMessage(testMessage)
      .execute(client);

    const receipt = await tx.getReceipt(client);

    console.log("✅ Message submitted successfully!");
    console.log("- Transaction ID:", tx.transactionId.toString());
    console.log("- Topic Sequence Number:", receipt.topicSequenceNumber?.toString());
    console.log("- Status:", receipt.status.toString());

    // Test reading from topic
    console.log("\n📖 Checking topic messages...");
    console.log("You can verify this message at:");
    console.log(`https://previewnet.mirrornode.hedera.com/api/v1/topics/${topicId}/messages`);

    client.close();

  } catch (error) {
    console.error("❌ Test failed:", error.message);
    console.error("Full error:", error);
  }
}

testHederaLogging();