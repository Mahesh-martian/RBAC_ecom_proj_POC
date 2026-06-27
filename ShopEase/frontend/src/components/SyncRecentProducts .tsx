import { useEffect } from "react";
import { useSelector } from "react-redux";
import { RootState } from "@/redux/store";
import { useSendRecentProductsMutation } from "@/redux/api/recentProducts";

const SyncRecentProducts = () => {
  const recentProducts = useSelector(
    (state: RootState) => state.recentProducts.productIds,
  );
  const [sendRecentProducts] = useSendRecentProductsMutation();

  useEffect(() => {
    const auth = localStorage.getItem("auth");
    if (auth) {
      if (recentProducts.length > 0) {
        sendRecentProducts([...recentProducts])
          .unwrap()
          .then(() => {
            console.log("Recent products successfully sent to the API.");
          })
          .catch((error) => {
            console.error("Error sending recent products to the API:", error);
          });
      }
    }
  }, [recentProducts, sendRecentProducts]);

  return null;
};

export default SyncRecentProducts;
