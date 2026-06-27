import { Secret } from "jsonwebtoken";
import config from "../../../config";
import { jwtHelpers } from "../../../helpers/jwtHelpers";
import prisma from "../../../shared/prisma";
import ApiError from "../../errors/ApiError";
import bcrypt from "bcrypt";
import emailSender from "../../../helpers/emailSender";
import {
  checkAccountStatus,
  findUserByEmail,
  findUserById,
} from "../../../helpers/userHelpers";
type TRegister = {
  name: string;
  email: string;
  password: string;
  role: "CUSTOMER" | "VENDOR" | "ADMIN";
};
type TLogin = {
  email: string;
  password: string;
};
type TChangePassword = {
  oldPassword: string;
  newPassword: string;
};

const register = async (payload: TRegister) => {
  // Check user exist with email
  // hash password
  // save user
  // create vender/customer
  const { name, email, password, role } = payload;

  const existingUser = await prisma.user.findUnique({
    where: {
      email,
    },
  });

  if (existingUser) {
    throw new ApiError(400, "User with this email already exists");
  }

  const hashedPassword = await bcrypt.hash(password, 10);

  return await prisma.$transaction(async (p) => {
    const newUser = await p.user.create({
      data: {
        name,
        email,
        password: hashedPassword,
        role,
      },
    });

    if (role === "VENDOR") {
      await p.vendor.create({
        data: {
          name,
          email: newUser.email,
        },
      });
    } else if (role === "CUSTOMER") {
      await p.customer.create({
        data: {
          name,
          email,
        },
      });
    } else if (role === "ADMIN") {
      await p.admin.create({
        data: {
          name,
          email,
        },
      });
    }

    // Exclude the password from the response
    const { password: _, ...userWithoutPassword } = newUser;
    return userWithoutPassword;
  });
};

const login = async (payload: TLogin) => {
  // find user
  // check whether password correct
  // generate access and refresh token
  // return data
  const { email, password } = payload;

  const user = await findUserByEmail(email);

  checkAccountStatus(user);

  const isPasswordValid = await bcrypt.compare(password, user.password);

  if (!isPasswordValid) throw new ApiError(401, "Invalid Credentials.");


  const { password: _, ...userWithoutPassword } = user;

  const accessToken = jwtHelpers.generateToken(
    userWithoutPassword,
    config.jwt.jwt_secret as Secret,
    config.jwt.expires_in as string
  );

  const refreshToken = jwtHelpers.generateToken(
    userWithoutPassword,
    config.jwt.refresh_token_secret as Secret,
    config.jwt.refresh_token_expires_in as string
  );


  return {
    accessToken,
    refreshToken,
    userWithoutPassword,
  };
};

const changePassword = async (user: any, payload: TChangePassword) => {
  // find user
  // check old password
  // hash new password
  // update new password
  const { newPassword, oldPassword } = payload;
  const { email } = user;

  const userData = await findUserByEmail(email);

  const isPasswordValid = await bcrypt.compare(oldPassword, userData.password);

  if (!isPasswordValid) throw new ApiError(401, "Invalid Credentials.");

  const hashedPassword = await bcrypt.hash(newPassword, 10);

  await prisma.user.update({
    where: { email: userData.email },
    data: {
      password: hashedPassword,
    },
  });

  return;
};

const forgotPassword = async (payload: { email: string }) => {
  // get email
  // find user
  // generate token
  // generate link
  // send email
  const user = await findUserByEmail(payload.email);

  checkAccountStatus(user);

  const resetPasswordToken = jwtHelpers.generateToken(
    { email: user.email, role: user.role },
    config.jwt.reset_pass_secret as Secret,
    config.jwt.reset_pass_token_expires_in as string
  );

  const resetPasswordLink = `${config.reset_pass_link}?userId=${user.id}&token=${resetPasswordToken}`;

  await emailSender(
    user.email,
    `
    <div>
    <p>Dear ${user.name}</p>
    <p> Your password reset link 
    <a href=${resetPasswordLink}>
    <button>Reset Password</button>
    </a>
    </p>
    </div>
    `
  );
};

const resetPassword = async (
  token: string,
  payload: { id: string; password: string }
) => {
  // find user with email
  // verify token
  // hash password
  // update password

  const user = await findUserById(payload.id);


  checkAccountStatus(user);



  const isValidToken = jwtHelpers.verifyToken(
    token,
    config.jwt.reset_pass_secret as Secret
  );


  if (!isValidToken) throw new ApiError(403, "Forbidden");

  const hashedPassword = await bcrypt.hash(payload.password, 10);

  await prisma.user.update({
    where: { id: payload.id },
    data: { password: hashedPassword },
  });
};

export const AuthServices = {
  register,
  login,
  changePassword,
  resetPassword,
  forgotPassword,
};
