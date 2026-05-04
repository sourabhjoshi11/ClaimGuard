import { getWorkflowAnomalies, type Claim, type UploadResponse, type WorkflowResult } from "@/lib/api";
import { formatRupees } from "@/lib/currency";

type ReportClaim = Pick<Claim, "id" | "status" | "media_type" | "created_at"> & {
  workflow_result?: WorkflowResult | null;
};

function escapePdfText(value: string): string {
  return value
    .replace(/[^\x20-\x7E]/g, "-")
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)");
}

function buildLines(claim: ReportClaim): string[] {
  const workflow = claim.workflow_result;
  const anomalies = getWorkflowAnomalies(workflow);
  const lines = [
    "ClaimGuard AI Assessment Report",
    `Claim: #${claim.id}`,
    `Status: ${workflow?.status || claim.status || "Unknown"}`,
    `Media type: ${claim.media_type || "image"}`,
    `Submitted: ${claim.created_at ? new Date(claim.created_at).toLocaleString() : new Date().toLocaleString()}`,
    `Total estimate: ${formatRupees(workflow?.total_claim_value)}`,
    `Detected anomalies: ${anomalies.length}`,
    "",
  ];

  if (anomalies.length === 0) {
    lines.push("No anomalies were detected.");
    return lines;
  }

  anomalies.forEach((item, index) => {
    lines.push(`${index + 1}. ${item.item || "Item"}`);
    lines.push(`   Issue: ${item.issue || "Not specified"}`);
    lines.push(`   Severity: ${item.severity || "Unknown"}`);
    lines.push(`   Estimated cost: ${formatRupees(item.estimated_cost)}`);
    lines.push("");
  });

  return lines;
}

export function claimFromUpload(result: UploadResponse): ReportClaim {
  return {
    id: result.claim_id,
    status: result.workflow_result.status,
    media_type: result.media_type,
    workflow_result: result.workflow_result,
  };
}

export function downloadClaimPdf(claim: ReportClaim) {
  const pageHeight = 792;
  const linesPerPage = 38;
  const rawLines = buildLines(claim);
  const pages = Array.from({ length: Math.ceil(rawLines.length / linesPerPage) }, (_, index) =>
    rawLines.slice(index * linesPerPage, (index + 1) * linesPerPage),
  );

  const objects: string[] = [];
  objects.push("<< /Type /Catalog /Pages 2 0 R >>");
  objects.push(`<< /Type /Pages /Kids [${pages.map((_, index) => `${3 + index * 2} 0 R`).join(" ")}] /Count ${pages.length} >>`);

  pages.forEach((lines, index) => {
    const pageObjectId = 3 + index * 2;
    const contentObjectId = pageObjectId + 1;
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> /F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> >> >> /Contents ${contentObjectId} 0 R >>`,
    );

    const body = lines
      .map((line, lineIndex) => {
        const y = pageHeight - 58 - lineIndex * 18;
        const font = lineIndex === 0 && index === 0 ? "/F2 18 Tf" : "/F1 10 Tf";
        return `BT ${font} 54 ${y} Td (${escapePdfText(line)}) Tj ET`;
      })
      .join("\n");

    objects.push(`<< /Length ${body.length} >>\nstream\n${body}\nendstream`);
  });

  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(pdf.length);
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });

  const xrefStart = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  offsets.slice(1).forEach((offset) => {
    pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
  });
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF`;

  const blob = new Blob([pdf], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `claimguard-claim-${claim.id}-report.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
