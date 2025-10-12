import {
  Client,
  PrivateKey,
  TopicMessageSubmitTransaction,
} from "@hashgraph/sdk";
import { VercelRequest, VercelResponse } from "@vercel/node";
import "dotenv/config";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const { log_message } = req.body;

  if (!log_message) {
    return res
      .status(400)
      .json({ error: "Missing 'log_message' in request body." });
  }

  try {
    const accountId = process.env.HEDERA_ACCOUNT_ID;
    const privateKeyStr = process.env.HEDERA_PRIVATE_KEY;
    const topicId = process.env.HEDERA_TOPIC_ID;

    if (!accountId || !privateKeyStr || !topicId) {
      console.error("HCS Error: Hedera environment variables not set.");
      return res
        .status(200)
        .json({
          status: "skipped",
          message: "Hedera logging is not configured on the server.",
        });
    }

    const privateKey = PrivateKey.fromString(privateKeyStr);

    const client = Client.forTestnet();
    client.setOperator(accountId, privateKey);

    const tx = await new TopicMessageSubmitTransaction()
      .setTopicId(topicId)
      .setMessage(log_message)
      .execute(client);

    const receipt = await tx.getReceipt(client);

    const logResult = {
      status: "success",
      sequenceNumber: receipt.topicSequenceNumber?.toString() || "N/A",
    };

    console.log("HCS Log successful:", logResult);

    return res.status(200).json(logResult);
  } catch (error: any) {
    console.error("HCS Error:", error);
    return res.status(200).json({ status: "error", message: error.message });
  }
}
