import { gql, useApolloClient } from "@apollo/client";
import { Box, Button, Text } from "@saleor/macaw-ui-next";
import { useState } from "react";

const VOUCHERS_QUERY = gql`
  query PracticeVouchers {
    vouchers(first: 100) {
      edges {
        node {
          id
          name
          type
          discountValueType
          startDate
          endDate
          usageLimit
          codes(first: 100) {
            edges {
              node {
                code
                used
                isActive
              }
            }
          }
          channelListings {
            channel {
              name
              currencyCode
            }
            discountValue
          }
        }
      }
    }
  }
`;

interface PracticeVoucher {
  id: string;
  name: string | null;
  type: string;
  discountValueType: string;
  startDate: string | null;
  endDate: string | null;
  usageLimit: number | null;
  codes?: {
    edges: Array<{ node: { code: string; used: number; isActive: boolean } }>;
  } | null;
  channelListings?: Array<{
    channel: { name: string; currencyCode: string };
    discountValue: number;
  }> | null;
}

const formatDate = (value: string | null) =>
  value ? new Date(value).toLocaleDateString() : "—";

export const CouponPracticeButton = () => {
  const client = useApolloClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vouchers, setVouchers] = useState<PracticeVoucher[]>([]);
  const [hasFetched, setHasFetched] = useState(false);

  const handleListCoupons = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await client.query({
        query: VOUCHERS_QUERY,
        fetchPolicy: "network-only",
      });
      const nodes: PracticeVoucher[] =
        result.data?.vouchers?.edges?.map((edge: any) => edge.node) ?? [];
      // Solo cupones cuyos códigos suman más de 0 usos.
      const usedVouchers = nodes.filter(
        voucher =>
          (voucher.codes?.edges.reduce((sum, e) => sum + (e.node.used ?? 0), 0) ?? 0) > 0,
      );
      setVouchers(usedVouchers);
      setHasFetched(true);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const renderDiscount = (voucher: PracticeVoucher) => {
    const listings = voucher.channelListings ?? [];
    if (listings.length === 0) {
      return voucher.discountValueType === "PERCENTAGE" ? "—%" : "—";
    }
    return listings
      .map(listing =>
        voucher.discountValueType === "PERCENTAGE"
          ? `${listing.discountValue}% (${listing.channel.name})`
          : `${listing.discountValue} ${listing.channel.currencyCode} (${listing.channel.name})`,
      )
      .join(", ");
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      gap={4}
      padding={6}
      marginTop={6}
      borderRadius={3}
      borderWidth={1}
      borderStyle="solid"
      borderColor="default1"
    >
      <Box display="flex" alignItems="center" gap={4}>
        <Button variant="primary" data-test-id="list-coupons-button" onClick={handleListCoupons}>
          Mostrar cupones que han tenido uso
        </Button>
        {loading && <Text color="default2">Cargando...</Text>}
        {hasFetched && !loading && !error && (
          <Text fontWeight="bold">{vouchers.length} cupones con uso</Text>
        )}
      </Box>

      {error && <Text color="critical1">Error: {error}</Text>}

      {vouchers.length > 0 && (
        <Box display="flex" flexDirection="column" gap={3}>
          {vouchers.map(voucher => {
            const codeNodes = voucher.codes?.edges.map(edge => edge.node) ?? [];
            const totalUsed = codeNodes.reduce((sum, c) => sum + (c.used ?? 0), 0);
            const wasUsed = totalUsed > 0;

            return (
              <Box
                key={voucher.id}
                display="flex"
                flexDirection="column"
                gap={1}
                padding={4}
                borderRadius={3}
                borderWidth={1}
                borderStyle="solid"
                borderColor="default1"
                backgroundColor="default1"
              >
                <Box display="flex" alignItems="center" gap={2}>
                  <Text size={4} fontWeight="bold">
                    {voucher.name || "(sin nombre)"}
                  </Text>
                  <Text size={2} color={wasUsed ? "success1" : "default2"}>
                    {wasUsed ? `✅ Usado (${totalUsed})` : "○ Sin usar"}
                  </Text>
                </Box>
                <Text size={2} color="default2">
                  Códigos:{" "}
                  {codeNodes.length > 0
                    ? codeNodes
                        .map(
                          c => `${c.code} — ${c.used} uso(s)${c.isActive ? "" : " (inactivo)"}`,
                        )
                        .join(" · ")
                    : "—"}
                </Text>
                <Text size={2} color="default2">
                  Tipo: {voucher.type} · Descuento: {voucher.discountValueType} ·{" "}
                  {renderDiscount(voucher)}
                </Text>
                <Text size={2} color="default2">
                  Vigencia: {formatDate(voucher.startDate)} → {formatDate(voucher.endDate)} ·
                  Límite de uso: {voucher.usageLimit ?? "ilimitado"}
                </Text>
              </Box>
            );
          })}
        </Box>
      )}
    </Box>
  );
};

export default CouponPracticeButton;
