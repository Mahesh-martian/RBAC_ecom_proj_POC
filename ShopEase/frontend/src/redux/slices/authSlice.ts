import { AuthState, BackendUser, User, UserWithoutPassword } from "@/types";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

const getInitialUser = (): User | null => {
  if (typeof window !== "undefined") {
    const userData = localStorage.getItem("auth");
    return userData ? JSON.parse(userData) : null;
  }
  return null;
};

const initialState: AuthState = {
  user: getInitialUser(),
};

const customizeUser = (user: UserWithoutPassword): User => {
  const { name, email, id: userId, role, vendor, customer } = user;

  // Determine the source of profilePhoto
  const profilePhoto = vendor?.profilePhoto || customer?.profilePhoto || null;

  const customizedUser: User = {
    name,
    email,
    userId,
    role,
    profilePhoto,
    vendorId: "",
    customerId: "",
  };

  // Add vendorId if role is not ADMIN and vendor exists
  if (role !== "ADMIN" && vendor) {
    customizedUser.vendorId = vendor.id;
  }

  // Add customerId if role is not ADMIN and customer exists
  if (role !== "ADMIN" && customer) {
    customizedUser.customerId = customer.id;
  }

  return customizedUser;
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuth(state, action: PayloadAction<BackendUser>) {
      const customizedUser = customizeUser(action.payload.userWithoutPassword);
      const accessToken = action.payload.accessToken;
      const refreshToken = action.payload.refreshToken;

      state.user = customizedUser;
     
      // Save user data to localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem("auth", JSON.stringify(customizedUser));
        localStorage.setItem("accessToken", JSON.stringify(accessToken));
        localStorage.setItem("refreshToken", JSON.stringify(refreshToken));
      }
    },
    logout(state) {
      state.user = null;

      // Remove user data from localStorage
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth");
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
      }
    },
  },
});

export const { setAuth, logout } = authSlice.actions;
export default authSlice.reducer;
